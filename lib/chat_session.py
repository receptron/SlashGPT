from lib.chat_config import ChatConfig
from lib.common import llms

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

from lib.log import create_log_dir, save_log
from lib.manifest import Manifest

"""
ChatSession represents a chat session with a particular AI agent.
The key is the identifier of the agent.
The manifest specifies behaviors of the agent.
"""
class ChatSession:
    def __init__(self, config: ChatConfig, manifest_key: str = "GPT"):
        self.config = config
        self.manifest_key = manifest_key

        self.set_manifest()

        self.time = datetime.now()
        self.userName = self.manifest.username()
        self.botName = self.manifest.botname()
        self.title = self.manifest.title()
        self.intro = self.manifest.get("intro")
        self.actions = self.manifest.actions()
        self.temperature = self.manifest.temperature()
        
        self.messages = []
        # init log dir
        create_log_dir(manifest_key)

        # Load the model name and make it sure that we have required keys
        (self.model, self.max_token) = get_model_and_max_token(config, self.manifest)

        agents = self.manifest.get("agents")

        # Load the prompt, fill variables and append it as the system message
        self.prompt = self.manifest.prompt_data()
        if self.prompt:
            if agents:
                self.prompt = apply_agent(self.prompt, agents, self.config)
            self.messages = [{"role":"system", "content":self.prompt}]

        # Prepare embedded database index
        self.index = None
        embeddings = self.manifest.get("embeddings")
        if embeddings:
            table_name = embeddings.get("name")
            if table_name and self.config.PINECONE_API_KEY and self.config.PINECONE_ENVIRONMENT:
                assert table_name in pinecone.list_indexes(), f"No Pinecone table named {table_name}"
                self.index = pinecone.Index(table_name)

        # Load agent specific python modules (for external function calls) if necessary
        self.module = self.manifest.read_module()
        
        # Load functions file if it is specified
        self.functions = self.manifest.function()
        if self.functions:
            if agents:
                # WARNING: It assumes that categorize(category, ...) function
                for function in self.functions:
                    if function.get("name") == "categorize":
                        function["parameters"]["properties"]["category"]["enum"] = agents

            if self.config.verbose:
                print(self.functions)

    def set_manifest(self):
        manifest_data = self.config.get_manifest_data(self.manifest_key)
        self.manifest = Manifest(manifest_data if manifest_data else {}, self.manifest_key)

    def set_model(self, model, max_token = 4096):
        self.model = model
        self.max_token = max_token
        print(f"Model = {self.model}")

    def get_manifest_attr(self, key):
        return self.manifest.get(key)

    def get_module(self, function_name):
        return self.module and self.module.get(function_name) or None

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
    def append_message(self, role: str, message: str, name = None):
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

    def save_log(self):
        save_log(self.manifest_key, self.messages, self.time)

    def set_intro(self):
        if self.intro:
            intro = self.intro[random.randrange(0, len(self.intro))]
            self.append_message("assistant", intro)
            print(f"\033[92m\033[1m{self.botName}\033[95m\033[0m: {intro}")

    """
    Extract the Python code from the string if the agent is a code interpreter.
    Returns it in the "function call" format. 
    """
    def _extract_function_call(self, res:str):
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
    def generate_response(self):
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
                (function_call, res) = self._extract_function_call(res)
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
            if llms.get(self.model):
                llm = llms.get(self.model)
                if llm.get("replicate_model"):
                    replicate_model = llm.get("replicate_model")
                
            output = replicate.run(
                replicate_model,
                input={"prompt": '\n'.join(prompts)},
                temperature = self.temperature
            )
            (function_call, res) = self._extract_function_call(''.join(output))

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
Get module name from manifest and set max_token.
"""
def get_model_and_max_token(config: ChatConfig, manifest = {}): 
    max_token = 4096
    model = manifest.model()
    if model == "gpt-3.5-turbo-16k-0613":
        return (model, max_token * 4)
    elif model == "palm":
        if config.GOOGLE_PALM_KEY is not None:
            return (model, max_token)
        print(colored("Please set GOOGLE_PALM_KEY in .env file","red"))
    elif model[:6] == "llama2":
        if config.REPLICATE_API_TOKEN is not None:
            return (model, max_token)
        print(colored("Please set REPLICATE_API_TOKEN in .env file","red"))
    return ("gpt-3.5-turbo-0613", max_token)

    


def apply_agent(prompt, agents, config):    
    descriptions = [f"{agent}: {config.manifests[agent].get('description')}" for agent in agents]
    return re.sub("\\{agents\\}", "\n".join(descriptions), prompt, 1)

