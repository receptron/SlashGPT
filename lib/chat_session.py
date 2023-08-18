from lib.chat_config import ChatConfig
from datetime import datetime
import re
import json
import openai
import random
import pinecone
import tiktoken  # for counting tokens
import google.generativeai as palm
import google.generativeai.types as safety_types
from termcolor import colored
import replicate

"""
ChatSession represents a chat session with a particular AI agent.
The key is the identifier of the agent.
The manifest specifies behaviors of the agent.
"""
class ChatSession:
    def __init__(self, config: ChatConfig, manifest_key: str = "GPT", manifest = {}):
        self.config = config
        self.manifest_key = manifest_key
        self.manifest = manifest
        self.time = datetime.now()
        self.userName = manifest.get("you") or f"You({manifest_key})"
        self.botName = manifest.get("bot") or "GPT"
        self.title = manifest.get("title") or ""
        self.intro = manifest.get("intro")
        self.messages = []
        self.actions = manifest.get("actions") or {} 

        self.temperature = 0.7
        if manifest.get("temperature"):
            self.temperature = float(manifest.get("temperature"))

        # Load the model name and make it sure that we have required keys
        (self.model, self.max_token) = get_model_and_max_token(config, manifest)

        agents = manifest.get("agents")

        # Load the prompt, fill variables and append it as the system message
        self.prompt = read_prompt(manifest)
        if self.prompt:
            data = get_manifest_data(manifest)
            if data:
                self.prompt = replace_random(self.prompt, data)
            resource = manifest.get("resource")
            if resource:
                self.prompt = replace_from_resource_file(self.prompt, resource)
            if agents:
                self.prompt = apply_agent(self.prompt, agents, self.config)
            self.messages = [{"role":"system", "content":self.prompt}]

        # Prepare embedded database index
        self.index = None
        embeddings = manifest.get("embeddings")
        if embeddings:
            table_name = embeddings.get("name")
            if table_name and self.config.PINECONE_API_KEY and self.config.PINECONE_ENVIRONMENT:
                assert table_name in pinecone.list_indexes(), f"No Pinecone table named {table_name}"
                self.index = pinecone.Index(table_name)

        # Load agent specific python modules (for external function calls) if necessary
        self.module = None
        module = manifest.get("module")
        if module:
            self.module = read_module(module)

        # Load functions file if it is specified
        self.functions = None
        functions_file = manifest.get("functions")
        if functions_file:
            with open(functions_file, 'r') as f:
                self.functions = json.load(f)
                if agents:
                    # WARNING: It assumes that categorize(category, ...) function
                    for function in self.functions:
                        if function.get("name") == "categorize":
                            function["parameters"]["properties"]["category"]["enum"] = agents

                if self.config.verbose:
                    print(self.functions)

    def set_model(self, model, max_token = 4096):
        self.model = model
        self.max_token = max_token
        print(f"Model = {self.model}")
    
    # Returns the number of tokens in a string
    def _num_tokens(self, text: str) -> int:
        encoding = tiktoken.encoding_for_model(self.model)
        return len(encoding.encode(text))

    # Returns the total number of tokens in messages    
    def _messages_tokens(self) -> int:
        return sum([self._num_tokens(message["content"]) for message in self.messages])

    # Fetch artciles related to user messages    
    def _fetch_related_articles(
        self,
        token_budget: int
    ) -> str:
        """Return related articles with the question using the embedding vector search."""
        query = ""
        for message in self.messages:
            if message["role"] == "user":
                query = message["content"] + "\n" + query
        query_embedding_response = openai.Embedding.create(
            model=self.config.EMBEDDING_MODEL,
            input=query,
        )
        query_embedding = query_embedding_response["data"][0]["embedding"]

        results = self.index.query(query_embedding, top_k=12, include_metadata=True)

        articles = ""
        count = 0
        base = self._messages_tokens()
        if self.config.verbose:
            print(f"messages token:{base}")
        for match in results["matches"]:
            string = match["metadata"]["text"]
            next_article = f'\n\nSection:\n"""\n{string}\n"""'
            if self._num_tokens(articles + next_article + query) + base > token_budget:
                break
            else:
                count += 1
                articles += next_article
                if self.config.verbose:
                    print(len(string), self._num_tokens(string))
        if self.config.verbose:
            print(f"Articles:{count}, Tokens:{self._num_tokens(articles + query)}")
        return articles

    """
    Append a message to the chat session, specifying the role ("user", "system" or "function").
    In case of a function message, the name specifies the function name.
    """
    def appendMessage(self, role: str, message: str, name = None):
        if name:
            self.messages.append({"role":role, "content":message, "name":name })
        else:
            self.messages.append({"role":role, "content":message })
        if self.index and role == "user":
            articles = self._fetch_related_articles(self.max_token - 500)
            assert self.messages[0]["role"] == "system", "Missing system message"
            self.messages[0] = {
                "role":"system", 
                "content":re.sub("\\{articles\\}", articles, self.prompt, 1)
            }

    """
    Extract the Python code from the string if the agent is a code interpreter.
    Returns it in the "function call" format. 
    """
    def _extractFunctionCall(self, res:str):
        if self.manifest.get("notebook"):
            lines = res.splitlines()
            codes = None
            for line in lines:
                if line[:3] == "```":
                    if codes is None:
                        codes = []
                    else:
                        break
                elif codes is not None:
                    codes.append(line)
            if codes:
                return ({
                    "name": "run_python_code",
                    "arguments": {
                        "code": codes,
                        "query": self.messages[-1]["content"]
                    }
                }, None) 
            
            print(colored("Debug Message: no code in this reply", "yellow"))
        return (None, res)

    """
    Let the LLM generate a responce based on the messasges in this session.
    Return values:
        role: "assistent"
        res: message
        function_call: json representing the function call (optional)
    """
    def generateResponse(self):
        role = None
        res = None
        function_call = None
        role = "assistant"

        if self.model == "palm":
            defaults = {
                'model': 'models/chat-bison-001',
                'temperature': self.temperature,
                'candidate_count': 1,
                'top_k': 40,
                'top_p': 0.95,
            }
            system = ""
            examples = []
            messages = []
            for message in self.messages:
                role = message["role"]
                content = message["content"]
                if content:
                    if role == "system":
                        system = message["content"]
                    elif len(messages)>0 or role != "assistant":
                        messages.append(message["content"])

            response = palm.chat(
                **defaults,
                context=system,
                examples=examples,
                messages=messages
            )
            res = response.last
            if res:
                if self.config.verbose:
                    print(colored(res, "magenta"))
                (function_call, res) = self._extractFunctionCall(res)
            else:
                # Error: Typically some restrictions
                print(colored(response.filters, "red"))

        elif self.model[:6] == "llama2" or self.model == "vicuna":
            prompts = []
            for message in self.messages:
                role = message["role"]
                content = message["content"]
                if content:
                    prompts.append(f"{role}:{message['content']}")
            if self.functions:
                last = prompts.pop()
                prompts.append(f"system: Here is the definition of functions available to you to call.\n{self.functions}\nYou need to generate a json file with 'name' for function name and 'arguments' for argument.")
                prompts.append(last)
            prompts.append("assistant:")

            replicate_model = "a16z-infra/llama7b-v2-chat:a845a72bb3fa3ae298143d13efa8873a2987dbf3d49c293513cd8abf4b845a83"
            if self.model == "llama270":
                replicate_model = "replicate/llama70b-v2-chat:2d19859030ff705a87c746f7e96eea03aefb71f166725aee39692f1476566d48"
            if self.model == "vicuna":
                replicate_model = "replicate/vicuna-13b:6282abe6a492de4145d7bb601023762212f9ddbbe78278bd6771c8b3b2f2a13b"
            output = replicate.run(
                replicate_model,
                input={"prompt": '\n'.join(prompts)},
                temperature = self.temperature
            )
            (function_call, res) = self._extractFunctionCall(''.join(output))

        else:
            if self.functions:
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=self.messages,
                    functions=self.functions,
                    temperature=self.temperature)
            else:
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=self.messages,
                    temperature=self.temperature)
            if self.config.verbose:
                print(colored(f"model={response['model']}", "yellow"))
                print(colored(f"usage={response['usage']}", "yellow"))
            answer = response['choices'][0]['message']
            res = answer['content']
            role = answer['role']
            function_call = answer.get('function_call')
        return (role, res, function_call)

"""
Read Module
Read Python file if module is in manifest.
"""
def read_module(module: str):
  with open(f"{module}", 'r') as f:
      try:
          code = f.read()
          namespace = {}
          exec(code, namespace)
          print(f" {module}")
          return namespace
      except ImportError:
          print(f"Failed to import module: {module}")

"""
Get module name from manifest and set max_token.
"""
def get_model_and_max_token(config: ChatConfig, manifest = {}): 
    max_token = 4096
    model = manifest.get("model") or "gpt-3.5-turbo-0613"
    if model == "gpt-3.5-turbo-16k-0613":
        return (model, max_token * 4)
    elif model == "palm":
        if config.GOOGLE_PALM_KEY is not None:
            return (mode, max_token)
        print(colored("Please set GOOGLE_PALM_KEY in .env file","red"))
    elif model[:6] == "llama2":
        if config.REPLICATE_API_TOKEN is not None:
            return (model, max_token)
        print(colored("Please set REPLICATE_API_TOKEN in .env file","red"))
    return ("gpt-3.5-turbo-0613", max_token)

"""
Read and create prompt string
"""
def read_prompt(manifest = {}):
    prompt = manifest.get("prompt")
    if isinstance(prompt,list):
        prompt = '\n'.join(prompt)
    if prompt:
        if re.search("\\{now\\}", prompt):
            time = datetime.now()
            prompt = re.sub("\\{now\\}", time.strftime('%Y%m%dT%H%M%SZ'), prompt, 1)
    return prompt            

"""
Read manifest data and shuffle data
"""
def get_manifest_data(manifest = {}):
    data = manifest.get("data")
    if data:
        # Shuffle 
        for i in range(len(data)):
            j = random.randrange(0, len(data))
            temp = data[i]
            data[i] = data[j]
            data[j] = temp
        return data
    
def replace_random(prompt, data):
    j = 0
    while(re.search("\\{random\\}", prompt)):
        prompt = re.sub("\\{random\\}", data[j], prompt, 1)
        j += 1
    return prompt

def replace_from_resource_file(prompt, resource_file_name):
    with open(f"{resource_file_name}", 'r') as f:
        contents = f.read()
        return re.sub("\\{resource\\}", contents, prompt, 1)

def apply_agent(prompt, agents, config):    
    descriptions = [f"{agent}: {config.manifests[agent].get('description')}" for agent in agents]
    return re.sub("\\{agents\\}", "\n".join(descriptions), prompt, 1)

