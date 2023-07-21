#!/usr/bin/env python3
import os
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
import my_jupyter as jp

# Configuration

class ChatConfig:
    def __init__(self):
        load_dotenv() # Load default environment variables (.env)
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        assert self.OPENAI_API_KEY, "OPENAI_API_KEY environment variable is missing from .env"
        self.GOOGLE_PALM_KEY = os.getenv("GOOGLE_PALM_KEY", None)
        self.EMBEDDING_MODEL = "text-embedding-ada-002"
        self.PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
        self.PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "")
        self.REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", None)
        self.verbose = False
        self.audio = None

        # Initialize OpenAI and optinoally Pinecone and Palm 
        openai.api_key = self.OPENAI_API_KEY
        if (self.PINECONE_API_KEY and self.PINECONE_ENVIRONMENT):
            pinecone.init(api_key=self.PINECONE_API_KEY, environment=self.PINECONE_ENVIRONMENT)
        if (self.GOOGLE_PALM_KEY):
            palm.configure(api_key=self.GOOGLE_PALM_KEY)
        self.ONELINE_HELP = "System Slashes: /new, /bye, /clear, /prompt, /sample, /gpt3, /gpt4, /palm, /verbose, /help"
        self.LONG_HELP = """
/new:       Start from the scratch
/bye:       Terminate the app
/clear:     Clear the current conversation
/prompt:    Display the current prompt
/sample:    Make the sample request
/gpt3:      Switch the model to gpt-3.5-turbo-0613
/gpt31:     Switch the model to gpt-3.5-turbo-16k-0613
/gpt4:      Switch the model to gpt-4-0613
/palm:      Switch the model to Google PaLM
/verbose:   Toggle verbose switch
/roles1:    Switch the manifest set to ones in prompts (original)
/roles2:    Switch the manifest set to ones in roles2
"""

class ChatContext:
    def __init__(self, config: ChatConfig, key: str = "GPT", manifest = {}, manifests = None):
        self.config = config
        self.key = key
        self.time = datetime.now()
        self.userName = f"You({key})"
        self.botName = "GPT"
        self.title = ""
        self.intro = None
        self.manifest = manifest
        self.prompt = None
        self.index = None # pinecone index
        self.temperature = 0.7
        self.model = "gpt-3.5-turbo-0613"
        self.max_token = 4096
        self.messages = []
        self.functions = None
        self.actions = {}
        self.module = None
        if len(manifest.keys()) > 0:
            self.userName = manifest.get("you") or self.userName
            self.botName = manifest.get("bot") or self.key
            self.model = manifest.get("model") or self.model
            if self.model == "gpt-3.5-turbo-16k-0613":
                self.max_token = 4096 * 4
            self.title = manifest.get("title")
            self.intro = manifest.get("intro")
            self.actions = manifest.get("actions") or {} 
            module = manifest.get("module")
            if module:
                with open(f"{module}", 'r') as f:
                    try:
                        code = f.read()
                        namespace = {}
                        exec(code, namespace)
                        self.module = namespace
                    except ImportError:
                        print(f"Failed to import module: {module}")
            if (manifest.get("temperature")):
                self.temperature = float(manifest.get("temperature"))
            self.prompt = '\n'.join(manifest["prompt"])
            if(re.search("\\{now\\}", self.prompt)):
                # not isoformat (notice that the timezone is hardcoded)
                self.prompt = re.sub("\\{now\\}", self.time.strftime('%Y%m%dT%H%M%SZ'), self.prompt, 1)
            
            data = manifest.get("data")
            if data:
                # Shuffle 
                for i in range(len(data)):
                    j = random.randrange(0, len(data))
                    temp = data[i]
                    data[i] = data[j]
                    data[j] = temp
                j = 0
                while(re.search("\\{random\\}", self.prompt)):
                    self.prompt = re.sub("\\{random\\}", data[j], self.prompt, 1)
                    j += 1
            resource = manifest.get("resource")
            if resource:
                with open(f"{resource}", 'r') as f:
                    contents = f.read()
                    self.prompt = re.sub("\\{resource\\}", contents, self.prompt, 1)
            agents = manifest.get("agents")
            if agents and manifests:
                agents = [f"{agent}:{manifests[agent].get('description')}" for agent in agents]
                self.prompt = re.sub("\\{agents\\}", "\n".join(agents), self.prompt, 1)
            embeddings = manifest.get("embeddings")
            if embeddings:
                table_name = embeddings.get("name")
                if table_name and self.config.PINECONE_API_KEY and self.config.PINECONE_ENVIRONMENT:
                    assert table_name in pinecone.list_indexes(), f"No Pinecone table named {table_name}"
                    self.index = pinecone.Index(table_name)

            self.messages = [{"role":"system", "content":self.prompt}]
            functions = manifest.get("functions")
            if functions:
                with open(f"{functions}", 'r') as f:
                    self.functions = json.load(f)
                    if self.config.verbose:
                        print(self.functions)

    def clearMessages(self):
        self.messages = self.messages[:1]

    def num_tokens(self, text: str) -> int:
        """Return the number of tokens in a string."""
        encoding = tiktoken.encoding_for_model(self.model)
        return len(encoding.encode(text))
    
    def messages_tokens(self) -> int:
        return sum([self.num_tokens(message["content"]) for message in self.messages])
    
    def fetch_related_articles(
        self,
        token_budget: int
    ) -> str:
        """Return related articles with the question using the embedding vector search."""
        query = ""
        for message in self.messages:
            if (message["role"] == "user"):
                query = message["content"] + "\n" + query
        query_embedding_response = openai.Embedding.create(
            model=self.config.EMBEDDING_MODEL,
            input=query,
        )
        query_embedding = query_embedding_response["data"][0]["embedding"]

        results = self.index.query(query_embedding, top_k=12, include_metadata=True)

        articles = ""
        count = 0
        base = self.messages_tokens()
        if (self.config.verbose):
            print(f"messages token:{base}")
        for match in results["matches"]:
            string = match["metadata"]["text"]
            next_article = f'\n\nSection:\n"""\n{string}\n"""'
            if (self.num_tokens(articles + next_article + query) + base > token_budget):
                break
            else:
                count += 1
                articles += next_article
                if self.config.verbose:
                    print(len(string), self.num_tokens(string))
        if (self.config.verbose):
            print(f"Articles:{count}, Tokens:{self.num_tokens(articles + query)}")
        return articles

    def appendQuestion(self, role: str, question: str, name):
        if name:
            self.messages.append({"role":role, "content":question, "name":name })
        else:
            self.messages.append({"role":role, "content":question })
        if self.index:
            articles = self.fetch_related_articles(self.max_token - 500)
            assert self.messages[0]["role"] == "system", "Missing system message"
            self.messages[0] = {
                "role":"system", 
                "content":re.sub("\\{articles\\}", articles, self.prompt, 1)
            }

    def processPython(self, output:str, original_question:str):
        if self.manifest.get("notebook"):
            res = ''.join(output)
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
                res = '\n'.join(codes) # Ignore except code
                res = f"Here is the code.\n```\n{res}\n```"
                self.messages.append({"role":"assistant", "content":res})
                print(f"\033[92m\033[1m{self.botName}\033[95m\033[0m: {res}")
                res = None # we have already appended it
                (function_result, foo) = jp.run_python_code(codes, original_question)
                function_result = f"Here is the result.\n\n{function_result}"
                print(f"\033[95m\033[1mFunction(function): \033[95m\033[0m{function_result}")
            else:
                print(colored("Debug Message: code code in this reply", "yellow"))

    """
    Let the LLM generate a message and append it to the message list
    returns (role, res) if a message was appended.
    """
    def generateResponse(self, original_question):
        role = None
        res = None
        function_call = None
        function_result = None
        if (self.model == "palm"):
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
                if (content):
                    if (role == "system"):
                        system = message["content"]
                    elif (len(messages)>0 or role != "assistant"):
                        messages.append(message["content"])

            response = palm.chat(
                **defaults,
                context=system,
                examples=examples,
                messages=messages
            )
            res = response.last
            if (res == None):
                print(response.filters)
            role = "assistant"
        elif (self.model == "palmt"):
            defaults = {
                'model': 'models/text-bison-001',
                'temperature': self.temperature,
                'candidate_count': 1,
                'top_k': 40,
                'top_p': 0.95,
            }
            prompts = []
            for message in self.messages:
                role = message["role"]
                content = message["content"]
                if (content):
                    if (role == "system"):
                        prompts.append(message["content"])
                    else:
                        prompts.append(f"{role}:{message['content']}")
            prompts.append("assistant:")
            response = palm.generate_text(
                **defaults,
                prompt='\n'.join(prompts)
            )
            res = response.result
            role = "assistant"
        elif (self.model == "llama2"):
            prompts = []
            for message in self.messages:
                role = message["role"]
                content = message["content"]
                if (content):
                    prompts.append(f"{role}:{message['content']}")
            if self.functions:
                last = prompts.pop()
                prompts.append(f"system: Here is the definition of functions available to you to call.\n{self.functions}\nYou need to generate a json file with 'name' for function name and 'arguments' for argument.")
                prompts.append(last)
            prompts.append("assistant:")

            output = replicate.run(
               "a16z-infra/llama7b-v2-chat:a845a72bb3fa3ae298143d13efa8873a2987dbf3d49c293513cd8abf4b845a83",
                input={"prompt": '\n'.join(prompts)}
            )

            res = self.processPython(output, original_question)
            role = "assistant"
        else:
            if self.functions:
                # print(colored(self.messages, "green"))
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
            if (self.config.verbose):
                print(colored(f"model={response['model']}", "yellow"))
                print(colored(f"usage={response['usage']}", "yellow"))
            answer = response['choices'][0]['message']
            res = answer['content']
            role = answer['role']
            function_call = answer.get('function_call')
        return (role, res, function_call, function_result)

class Main:
    def __init__(self, config: ChatConfig, pathManifests: str):
        self.config = config

        # Prepare output folders
        if not os.path.isdir("output"):
            os.makedirs("output")
        if not os.path.isdir("output/GPT"):
            os.makedirs("output/GPT")

        self.loadManifests(pathManifests)
        self.context = ChatContext(self.config)
        self.exit = False
        self.pathManifests = pathManifests

    def loadManifests(self, path):
        self.manifests = {}
        files = os.listdir(path)
        for file in files:
            key = file.split('.')[0]
            with open(f"{path}/{file}", 'r') as f:
                data = json.load(f)
            # print(key, file, data)
            self.manifests[key] = data

    def switchContext(self, key: str, intro: bool = True):
        self.key = key
        manifest = self.manifests.get(key)
        if manifest:
            self.context = ChatContext(self.config, key=key, manifest=manifest, manifests=self.manifests)
            if not os.path.isdir(f"output/{self.context.key}"):
                os.makedirs(f"output/{self.context.key}")
            if self.config.verbose:
                print(colored(f"Activating: {self.context.title} (model={self.context.model}, temperature={self.context.temperature}, max_token={self.context.max_token})", "blue"))
            else:
                print(colored(f"Activating: {self.context.title}", "blue"))
            isNotebook = manifest.get("notebook")
            if isNotebook:
                print(colored("Creating a notebook", "blue"))
                jp.create_notebook()

            if intro and self.context.intro:
                intro = self.context.intro[random.randrange(0, len(self.context.intro))]
                self.context.messages.append({"role":"assistant", "content":intro})
                print(f"\033[92m\033[1m{self.context.botName}\033[95m\033[0m: {intro}")
            return True
        else:            
            print(colored(f"Invalid slash command: {key}", "red"))
            return False

    """
    If the question start with "/", process it as a Slash command.
    Otherwise, return (roleInput, question) as is.
    Notice that some Slash commands returns (role, question) as well.
    """
    def processSlash(self, roleInput:str, question: str):
        if (len(question) == 0):
            print(self.config.ONELINE_HELP)
        elif (question[0] == "/"):
            key = question[1:]
            commands = key.split(' ')
            if (commands[0] == "help"):
                if (len(commands) == 1):
                    print(self.config.LONG_HELP)
                    list = "\n".join(f"/{(key+'         ')[:12]} {self.manifests[key].get('title')}" for key in sorted(self.manifests.keys()))
                    print(f"Agents:\n{list}")
                if (len(commands) == 2):
                    manifest = self.manifests.get(commands[1])
                    if (manifest):
                       print(json.dumps(manifest, indent=2))
            elif (key == "bye"):
                self.exit = True;
            elif (key == "verbose"):
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
            elif (key == "prompt"):
                if (len(self.context.messages) >= 1):
                    print(self.context.messages[0].get("content"))
                if self.config.verbose and self.context.functions:
                    print(self.context.functions)
            elif (key == "functions"):
                if self.context.functions:
                    print(json.dumps(self.context.functions, indent=2))
            elif (key == "gpt3"):
                self.context.model = "gpt-3.5-turbo-0613"
                self.context.max_token = 4096
                print(f"Model = {self.context.model}")
            elif (key == "gpt31"):
                self.context.model = "gpt-3.5-turbo-16k-0613"
                self.context.max_token = 4096 * 4
                print(f"Model = {self.context.model}")
            elif (key == "gpt4"):
                self.context.model = "gpt-4-0613"
                self.context.max_token = 4096
                print(f"Model = {self.context.model}")
            elif (key == "llama2"):
                if self.config.REPLICATE_API_TOKEN:
                    self.context.model = "llama2"
                    self.context.max_token = 4096
                    print(f"Model = {self.context.model}")
                else:
                    print(colored("You need to set REPLICATE_API_TOKEN to use this model","red"))
            elif (key == "palm"):
                if (self.config.GOOGLE_PALM_KEY):
                    self.context.model = "palm"
                    if (self.context.botName == "GPT"):
                        self.context.botName = "PaLM"
                    print(f"Model = {self.context.model}")
                else:
                    print("Error: Missing GOOGLE_PALM_KEY")
            elif (key == "palmt"):
                if (self.config.GOOGLE_PALM_KEY):
                    self.context.model = "palmt"
                    if (self.context.botName == "GPT"):
                        self.context.botName = "PaLM(Text)"
                    print(f"Model = {self.context.model}")
                else:
                    print("Error: Missing GOOGLE_PALM_KEY")
            elif commands[0] == "sample" and len(commands) > 1:
                sub_key = commands[1]
                sub_manifest = self.manifests.get(sub_key)
                if sub_manifest:
                    sample = sub_manifest.get("sample")
                    if sample:
                        print(sample)
                        return ("user", sample)
            elif key[:6] == "sample":
                sample = self.context.manifest.get(key)
                if (sample):
                    print(sample)
                    return ("user", sample)
                print(colored(f"Error: No {key} in the manifest file", "red"))
            elif (key == "new"):
                self.loadManifests(self.pathManifests)
                main.switchContext('dispatcher')
            elif (key == "clear"):
                if self.key:
                    self.switchContext(self.key)
                else:
                    self.context.clearMessages()
                bootstrap = self.context.manifest.get("bootstrap")
                if bootstrap:
                    return ("user", bootstrap)
            elif (key == "rpg1"):
                self.loadManifests('./rpg1')
                main.switchContext('bartender')
            elif (key == "roles1"):
                self.loadManifests('./prompts')
                self.context = ChatContext(self.config)
            elif (key == "roles2"):
                self.loadManifests('./roles2')
                self.context = ChatContext(self.config)
            else:
                if self.switchContext(key):
                    bootstrap = self.context.manifest.get("bootstrap")
                    if bootstrap:
                        return ("user", bootstrap)
        else:
            return (roleInput, question)
        return (None, None)
    
    def start(self):
        function_message = None
        name = None
        while not self.exit:
            roleInput = "user"
            form = None
            if function_message:
                if name:
                    roleInput = "function"
                question = function_message
                function_message = None
                if self.config.verbose:
                    print(f"\033[95m\033[1mFunction({name}): \033[95m\033[0m{question}")
            else:
                # Otherwise, retrieve the input from the user.
                question = input(f"\033[95m\033[1m{self.context.userName}: \033[95m\033[0m")
                name = None
                form = self.context.manifest.get("form")

            # Process slash commands (if exits)
            (role, question) = self.processSlash(roleInput, question)

            if role and question:
                original_question = question
                if form:
                    question = form.format(question = question)
                if self.config.verbose and role=="user":
                    print(f"\033[95m\033[1m{self.context.userName}/bootstrap: \033[95m\033[0m{question}")
                try:
                    self.context.appendQuestion(role, question, name)
                    # Ask LLM to generate a response.
                    (role, res, function_call, function_result) = self.context.generateResponse(original_question)

                    if role and res:
                        print(f"\033[92m\033[1m{self.context.botName}\033[95m\033[0m: {res}")

                        if self.config.audio:
                            audio_obj = gTTS(text=res, lang=self.config.audio, slow=False)
                            audio_obj.save("./output/audio.mp3")
                            playsound("./output/audio.mp3")

                        self.context.messages.append({"role":role, "content":res})
                        with open(f"output/{self.context.key}/{self.context.time}.json", 'w') as f:
                            json.dump(self.context.messages, f)

                    if function_result:
                        name = "call_python_code" #anything is fine actually
                        function_message = function_result
                    elif function_call:
                        name = function_call.get("name")
                        arguments = function_call.get("arguments") 
                        if arguments and isinstance(arguments, str):
                            try:
                                arguments = json.loads(arguments)      
                                function_call.arguments = arguments
                            except Exception as e:
                                print(colored(f"Function {name}: Failed to load arguments as json","yellow"))
                        if isinstance(arguments, str):
                            params = arguments
                        else:
                            params = ','.join(f"{key}={function_call.arguments[key]}" for key in function_call.arguments.keys())
                        print(colored(f"Function: {name}({params})", "blue"))
                        if name:
                            action = self.context.actions.get(name)
                            if action:
                                url = action.get("url")
                                method = action.get("method")
                                template = action.get("template")
                                message_template = action.get("message")
                                metafile = action.get("metafile")
                                appkey = action.get("appkey")
                                if metafile:
                                    metafile = metafile.format(**arguments)
                                    self.switchContext(metafile, intro = False)
                                    name = None # Withough name, this message will be treated as user prompt.
                                if appkey:
                                    appkey_value = os.getenv(appkey, "")
                                    if appkey_value:
                                        arguments["appkey"] = appkey_value
                                    else:
                                        print(colored(f"Missing {appkey} in .env file.", "red"))
                                if url:
                                    headers = action.get("headers",{})
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
                                        function_message = response.text
                                    else:
                                        print(colored(f"Got {response.status_code}:{response.text} from {url}", "red"))
                                elif template:
                                    mime_type = action.get("mime_type") or ""
                                    message_template = message_template or f"{url}"
                                    with open(f"{template}", 'r') as f:
                                        template = f.read()
                                        if self.config.verbose:
                                            print(template)
                                        ical = template.format(**arguments)
                                        url = f"data:{mime_type};charset=utf-8,{urllib.parse.quote_plus(ical)}"
                                        function_message = message_template.format(url = url)
                                elif message_template:
                                    function_message = message_template.format(**arguments)
                                else: 
                                    function_message = "Success"
                            else:
                                function = self.context.module and self.context.module.get(name) or None
                                if function:
                                    if isinstance(arguments, str):
                                        (result, message) = function(arguments)
                                    else:
                                        (result, message) = function(**arguments)
                                    if message:
                                        # Embed code for the context
                                        self.context.messages.append({"role":"assistant", "content":message})
                                        print(colored(message, "blue"))
                                    if isinstance(result, dict):
                                        result = json.dumps(result)
                                    function_message = result
                                else:
                                    print(colored(f"No function {name} in the module", "red"))
                except Exception as e:
                    print(colored(f"Exception: Restarting the chat :{e}","red"))
                    self.context.clearMessages()
                    if self.config.verbose:
                        raise

config = ChatConfig()
print(config.ONELINE_HELP)
main = Main(config, "./manifests")
main.switchContext('dispatcher')
main.start()

