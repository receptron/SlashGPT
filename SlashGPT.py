#!/usr/bin/env python3
import os
import platform
if platform.system() == "Darwin":
    import readline # So that input can handle Kanji & delete
import openai
from dotenv import load_dotenv
import json
from datetime import datetime
import re
import random
import pinecone
import tiktoken  # for counting tokens
import google.generativeai as palm
import google.generativeai.types as safety_types
from termcolor import colored
import urllib.parse
import requests
from gtts import gTTS
from playsound import playsound
import urllib.parse
import replicate
from jupyter_runtime import PythonRuntime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

# Configuration

LONG_HELP = """
/root:      Start from the scratch (going back to dispatcher)
/bye:       Terminate the app
/new:       Start a new chat session
/prompt:    Display the current prompt
/history:   Display the chat history
/sample:    Make the sample request
/gpt3:      Switch the model to gpt-3.5-turbo-0613
/gpt31:     Switch the model to gpt-3.5-turbo-16k-0613
/gpt4:      Switch the model to gpt-4-0613
/palm:      Switch the model to Google PaLM
/llama2:    Switch the model to LlaMA2 7b
/llama270:  Switch the model to LlaMA2 70b
/vicuna:    Switch the model to Vicuna 16b
/verbose:   Toggle verbose switch
/roles1:    Switch the manifest set to ones in prompts (original)
/roles2:    Switch the manifest set to ones in roles2
"""

"""
ChatConfig is a singleton, which holds global states, including various secret keys and the list of manifests.
"""
class ChatConfig:
    def __init__(self, pathManifests):
        # Load various keys from .env file
        load_dotenv() 
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        assert self.OPENAI_API_KEY, "OPENAI_API_KEY environment variable is missing from .env"
        self.GOOGLE_PALM_KEY = os.getenv("GOOGLE_PALM_KEY", None)
        self.EMBEDDING_MODEL = "text-embedding-ada-002"
        self.PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
        self.PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "")
        self.REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", None)

        # Initialize other settings and load all manifests
        self.verbose = False
        self.audio = None
        self.ONELINE_HELP = "System Slashes: /root, /bye, /new, /prompt, /sample, /help, ..."
        self.LONG_HELP = LONG_HELP
        self.loadManifests(pathManifests)

        # Initialize OpenAI and optinoally Pinecone and Palm 
        openai.api_key = self.OPENAI_API_KEY
        if self.PINECONE_API_KEY and self.PINECONE_ENVIRONMENT:
            pinecone.init(api_key=self.PINECONE_API_KEY, environment=self.PINECONE_ENVIRONMENT)
        if self.GOOGLE_PALM_KEY:
            palm.configure(api_key=self.GOOGLE_PALM_KEY)

    """
    Load a set of manifests. 
    It's called initially, but it's called also when the user makes a request to switch the set (such as roles1).
    """
    def loadManifests(self, path):
        self.manifests = {}
        files = os.listdir(path)
        for file in files:
            with open(f"{path}/{file}", 'r',encoding="utf-8") as f:	# encoding add for Win
                self.manifests[file.split('.')[0]] = json.load(f)

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
    descriptions = [f"{agent}:{config.manifests[agent].get('description')}" for agent in agents]
    return re.sub("\\{agents\\}", "\n".join(descriptions), prompt, 1)

    
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
utility functions for Main class
"""

def play_text(text, lang):
    audio_obj = gTTS(text=text, lang=lang, slow=False)
    audio_obj.save("./output/audio.mp3")
    playsound("./output/audio.mp3")

def save_log(manifest_key, messages, time):
    timeStr = time.strftime("%Y-%m-%d %H-%M-%S.%f")
    with open(f'output/{manifest_key}/{timeStr}.json', 'w') as f:   
        json.dump(messages, f)

"""
Main is a singleton, which process the input from the user and manage chat sessions.
"""
class Main:
    def __init__(self, config: ChatConfig):
        self.config = config

        # Prepare output folders
        if not os.path.isdir("output"):
            os.makedirs("output")
        if not os.path.isdir("output/GPT"):
            os.makedirs("output/GPT")

        self.context = ChatSession(self.config)
        self.exit = False
        self.runtime = PythonRuntime("./output/notebooks")

    """
    switchContext terminate the current chat session and start a new.
    The key specifies the AI agent.
    """
    def switchContext(self, manifest_key: str, intro: bool = True):
        if manifest_key is None:
            self.context = ChatSession(self.config)
        manifest = self.config.manifests.get(manifest_key)
        if manifest:
            self.context = ChatSession(self.config, manifest_key=manifest_key, manifest=manifest)
            if not os.path.isdir(f"output/{self.context.manifest_key}"):
                os.makedirs(f"output/{self.context.manifest_key}")
            if self.config.verbose:
                print(colored(f"Activating: {self.context.title} (model={self.context.model}, temperature={self.context.temperature}, max_token={self.context.max_token})", "blue"))
            else:
                print(colored(f"Activating: {self.context.title}", "blue"))
            isNotebook = manifest.get("notebook")
            if isNotebook:
                (result, _) = self.runtime.create_notebook(self.context.model)
                print(colored(f"Created a notebook: {result.get('notebook_name')}", "blue"))

            if intro and self.context.intro:
                intro = self.context.intro[random.randrange(0, len(self.context.intro))]
                self.context.appendMessage("assistant", intro)
                print(f"\033[92m\033[1m{self.context.botName}\033[95m\033[0m: {intro}")
        else:            
            print(colored(f"Invalid slash command: {manifest_key}", "red"))


    def processMode(self, question: str):
        key = question[1:]
        commands = key.split(' ')
        if len(question) == 0:
            return "help"
        elif commands[0] == "sample" and len(commands) > 1:
            return "sample"
        elif key[:6] == "sample":
            return "sample"
        elif question[0] == "/":
            return "slash"
        else:
            return "talk"

    def processHelp(self):
        print(self.config.ONELINE_HELP)

    def processSample(self, question: str):
        key = question[1:]
        commands = key.split(' ')
        if commands[0] == "sample" and len(commands) > 1:
            sub_key = commands[1]
            sub_manifest = self.config.manifests.get(sub_key)
            if sub_manifest:
                sample = sub_manifest.get("sample")
                if sample:
                    print(sample)
                    return ("user", sample)
        elif key[:6] == "sample":
            sample = self.context.manifest.get(key)
            if sample:
                print(sample)
                return ("user", sample)
            print(colored(f"Error: No {key} in the manifest file", "red"))
            
    """
    If the question start with "/", process it as a Slash command.
    Otherwise, return (roleInput, question) as is.
    Notice that some Slash commands returns (role, question) as well.
    """
    def processSlash(self, question: str):
        if question[0] == "/": # TODO remove
            key = question[1:]
            commands = key.split(' ')
            if commands[0] == "help":
                if (len(commands) == 1):
                    print(self.config.LONG_HELP)
                    list = "\n".join(f"/{(key+'         ')[:12]} {self.config.manifests[key].get('title')}" for key in sorted(self.config.manifests.keys()))
                    print(f"Agents:\n{list}")
                if (len(commands) == 2):
                    manifest = self.config.manifests.get(commands[1])
                    if (manifest):
                       print(json.dumps(manifest, indent=2))
            elif key == "bye":
                self.runtime.stop()
                self.exit = True;
            elif key == "verbose":
                self.config.verbose = self.config.verbose == False
                print(f"Verbose Mode: {self.config.verbose}")
            elif commands[0] == "audio":
                if len(commands) == 1:
                    if self.config.audio:
                        self.config.audio = None
                    else:
                        self.config.audio = "en"
                elif commands[1] == "off":
                    self.config.audio = None
                else:
                    self.config.audio = commands[1]
                print(f"Audio mode: {self.config.audio}")
            elif key == "prompt":
                if len(self.context.messages) >= 1:
                    print(self.context.messages[0].get("content"))
                if self.config.verbose and self.context.functions:
                    print(self.context.functions)
            elif key == "history":
                print(json.dumps(self.context.messages, indent=2))
            elif key == "functions":
                if self.context.functions:
                    print(json.dumps(self.context.functions, indent=2))
            elif key == "gpt3":
                self.context.set_model("gpt-3.5-turbo-0613")
            elif key == "gpt31":
                self.context.set_model("gpt-3.5-turbo-16k-0613", 4096 * 4)
            elif key == "gpt4":
                self.context.set_model("gpt-4-0613")
            elif key == "llama2" or key == "llama270" or key == "vicuna":
                if self.config.REPLICATE_API_TOKEN:
                    self.context.set_model(key)
                else:
                    print(colored("You need to set REPLICATE_API_TOKEN to use this model","red"))
            elif key == "palm":
                if self.config.GOOGLE_PALM_KEY:
                    self.context.set_model("palm")
                    if self.context.botName == "GPT":
                        self.context.botName = "PaLM"
                else:
                    print("Error: Missing GOOGLE_PALM_KEY")
            elif key == "root":
                self.config.loadManifests("./manifests")
                self.switchContext('dispatcher', intro = False)
            elif key == "new":
                self.switchContext(self.context.manifest_key, intro = False)
            elif key == "rpg1":
                self.config.loadManifests('./rpg1')
                self.switchContext('bartender')
            elif key == "zoo":
                self.config.loadManifests('./zoo')
                self.switchContext('monkey')
            elif key == "roles1":
                self.config.loadManifests('./prompts')
                self.context = ChatSession(self.config)
            elif key == "roles2":
                self.config.loadManifests('./roles2')
                self.context = ChatSession(self.config)
            else:
                self.switchContext(key)

    """
    the main loop
    """    
    def start(self):
        function_name = None
        is_next_function = False
        while not self.exit:
            roleInput = "function" if is_next_function else "user"
            form = None
            if is_next_function:
                print(f"\033[95m\033[1mfunction({function_name}): \033[95m\033[0m{question}")
                is_next_function = False
            else:
                # Otherwise, retrieve the input from the user.
                question = input(f"\033[95m\033[1m{self.context.userName}: \033[95m\033[0m")
                function_name = None
                if question[:1] == "`":
                    print(colored("skipping form", "blue"))
                    question = question[1:]
                else:
                    form = self.context.manifest.get("form")

            mode = self.processMode(question)
            if mode == "help":
                self.processHelp()
            elif mode == "slash":
                self.processSlash(question)
            elif mode == "sample" or mode == "talk":
                (role, question) = self.processSample(question) if mode == "sample" else (roleInput, question)
                if role and question:
                    if form:
                        question = form.format(question = question)
                    try:
                        self.context.appendMessage(role, question, function_name)
                        # Ask LLM to generate a response.
                        (responseRole, res, function_call) = self.context.generateResponse()

                        if responseRole and res:
                            print(f"\033[92m\033[1m{self.context.botName}\033[95m\033[0m: {res}")

                            if self.config.audio:
                                play_text(res, self.config.audio)

                            self.context.appendMessage(responseRole, res)
                            save_log(self.context.manifest_key, self.context.messages, self.context.time)

                        if function_call:
                            (question, function_name) = self.process_function_call(function_call)
                            if question and function_name:
                                is_next_function = True
                    except Exception as e:
                        print(colored(f"Exception: Restarting the chat :{e}","red"))
                        self.switchContext(self.context.manifest_key)
                        if self.config.verbose:
                            raise

                    
    def process_function_call(self, function_call):
        function_message = None
        function_name = function_call.get("name")
        arguments = function_call.get("arguments") 
        if arguments and isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)      
                function_call["arguments"] = arguments
            except Exception as e:
                print(colored(f"Function {function_name}: Failed to load arguments as json","yellow"))
                
        print(colored(json.dumps(function_call, indent=2), "blue"))
        '''
        if isinstance(arguments, str):
            params = arguments
        else:
            params = ','.join(f"{key}={function_call["arguments"][key]}" for key in function_call.arguments.keys())
        print(colored(f"Function: {function_name}({params})", "blue"))
        '''
        if function_name:
            action = self.context.actions.get(function_name)
            if action:
                url = action.get("url")
                template = action.get("template")
                message_template = action.get("message")
                metafile = action.get("metafile")
                appkey = action.get("appkey")
                if metafile:
                    metafile = metafile.format(**arguments)
                    self.switchContext(metafile, intro = False)
                    function_name = None # Withough name, this message will be treated as user prompt.

                if appkey:
                    appkey_value = os.getenv(appkey, "")
                    if appkey_value:
                        arguments["appkey"] = appkey_value
                    else:
                        print(colored(f"Missing {appkey} in .env file.", "red"))
                if url:
                    if action.get("graphQL"):
                        function_message = self.graphQLRequest(url, arguments)
                    else:
                        function_message = self.http_request(url, action.get("method"), action.get("headers",{}), arguments)
                elif template:
                    function_message = self.read_dataURL_template(template, action.get("mime_type"), message_template, arguments)
                elif message_template:
                    function_message = message_template.format(**arguments)
                else: 
                    function_message = "Success"
            else:
                if self.context.manifest.get("notebook"):
                    if function_name == "python" and isinstance(arguments, str):
                        print(colored("python function was called", "yellow"))
                        arguments = {
                            "code": arguments,
                            "query": self.context.messages[-1]["content"]
                        }
                        function = getattr(self.runtime, function_name)
                    else:
                        function = self.context.module and self.context.module.get(function_name) or None
                if function:
                    if isinstance(arguments, str):
                        (result, message) = function(arguments)
                    else:
                        (result, message) = function(**arguments)
                    if message:
                        # Embed code for the context
                        self.context.appendMessage("assistant", message)
                    if isinstance(result, dict):
                        result = json.dumps(result)
                    result_form = self.context.manifest.get("result_form")
                    if result_form:
                        function_message = result_form.format(result = result)
                    else:
                        function_message = result
                    if self.context.manifest.get("skip_function_result"):
                        print(f"\033[95m\033[1mfunction({function_name}): \033[95m\033[0m{function_message}")
                        self.context.appendMessage("function", function_message, function_name)
                        function_message = None
                else:
                    print(colored(f"No function {function_name} in the module", "red"))
        return (function_message, function_name)


    def graphQLRequest(self, url, arguments):
        transport = RequestsHTTPTransport(url=url, use_json=True)
        client = Client(transport=transport)
        query = arguments.get("query")
        graphQuery = gql(f"query {query}")
        try:
            response = client.execute(graphQuery)
            return json.dumps(response)
        except Exception as e:
            return str(e)

    def http_request(self, url, method, headers, arguments):
        headers = {key:value.format(**arguments) for key,value in headers.items()}
        if method == "POST":
            headers['Content-Type'] = 'application/json';
            if self.config.verbose:
                print(colored(f"Posting to {url} {headers}", "yellow"))
            response = requests.post(url, headers=headers, json=arguments)
        else:
            url = url.format(**{key:urllib.parse.quote(value) for key, value in arguments.items()})
            if self.config.verbose:
                print(colored(f"Fetching from {url}", "yellow"))
            response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            print(colored(f"Got {response.status_code}:{response.text} from {url}", "red"))

    def read_dataURL_template(self, template, mime_type, message_template, arguments):
        _mime_type = mime_type or ""
        message_template = message_template or f"{url}"
        with open(f"{template}", 'r') as f:
            template = f.read()
            if self.config.verbose:
                print(template)
            data = template.format(**arguments)
            dataURL = f"data:{_mime_type};charset=utf-8,{urllib.parse.quote_plus(data)}"
            return message_template.format(url = dataURL)
        

                
config = ChatConfig("./manifests")
print(config.ONELINE_HELP)
main = Main(config)
main.switchContext('dispatcher')
main.start()
