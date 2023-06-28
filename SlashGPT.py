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

        # Initialize OpenAI and optinoally Pinecone and Palm 
        openai.api_key = self.OPENAI_API_KEY
        if (self.PINECONE_API_KEY and self.PINECONE_ENVIRONMENT):
            pinecone.init(api_key=self.PINECONE_API_KEY, environment=self.PINECONE_ENVIRONMENT)
        if (self.GOOGLE_PALM_KEY):
            palm.configure(api_key=self.GOOGLE_PALM_KEY)
        self.ONELINE_HELP = "System Slashes: /bye, /reset, /prompt, /sample, /gpt3, /gpt4, /palm, /verbose, /help"

class ChatContext:
    def __init__(self, config: ChatConfig, role: str = "GPT", manifest = None):
        self.config = config
        self.role = role
        self.time = datetime.now()
        self.userName = "You"
        self.botName = "GPT"
        self.title = ""
        self.intro = None
        self.sample = None
        self.manifest = manifest
        self.prompt = None
        self.verbose = False
        self.index = None # pinecone index
        self.temperature = 0.7
        self.model = "gpt-3.5-turbo-0613"
        self.max_token = 4096
        self.messages = []
        self.functions = None
        self.actions = {}
        self.module = None
        if (manifest):
            self.userName = manifest.get("you") or self.userName
            self.botName = manifest.get("bot") or self.role
            self.model = manifest.get("model") or self.model
            if self.model == "gpt-3.5-turbo-16k-0613":
                self.max_token = 4096 * 4
            self.title = manifest.get("title")
            self.intro = manifest.get("intro")
            self.sample = manifest.get("sample")
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
                    if self.verbose:
                        print(self.functions)

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
        if (self.verbose):
            print(f"messages token:{base}")
        for match in results["matches"]:
            string = match["metadata"]["text"]
            next_article = f'\n\nWikipedia article section:\n"""\n{string}\n"""'
            if (self.num_tokens(articles + next_article + query) + base > token_budget):
                break
            else:
                count += 1
                articles += next_article
        if (self.verbose):
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

    """
    Let the LLM generate a message and append it to the message list
    returns (role, res) if a message was appended.
    """
    def generateResponse(self):
        role = None
        res = None
        function_call = None
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
            if (self.verbose):
                print(f"model={response['model']}")
                print(f"usage={response['usage']}")
            answer = response['choices'][0]['message']
            res = answer['content']
            role = answer['role']
            function_call = answer.get('function_call')
        return (role, res, function_call)

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

    def loadManifests(self, path):
        self.manifests = {}
        files = os.listdir(path)
        for file in files:
            key = file.split('.')[0]
            with open(f"{path}/{file}", 'r') as f:
                data = json.load(f)
            # print(key, file, data)
            self.manifests[key] = data

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
            if (key == "help"):
                list = ", ".join(f"/{key}" for key in self.manifests.keys())
                print(f"Extensions: {list}")
            elif (key == "bye"):
                self.exit = True;
            elif (key == "verbose"):
                self.context.verbose = self.context.verbose == False
                print(f"Verbose Mode: {self.context.verbose}")
            elif (key == "prompt"):
                if (len(self.context.messages) >= 1):
                    print(self.context.messages[0].get("content"))
                if self.context.verbose and self.context.functions:
                    print(self.context.functions)
            elif (key == "gpt3"):
                self.context.model = "gpt-3.5-turbo-0613"
                self.context.max_token = 4096
                print(f"Model = {self.context.model}")
            elif (key == "gpt31"):
                self.context.model = "gpt-3.5-turbo-16k-0613"
                self.context.max_token = 4096 * 4
                print(f"Model = {self.context.model}")
            elif (key == "gpt4"):
                self.context.model = "gpt-4"
                self.context.max_token = 4096
                print(f"Model = {self.context.model}")
            elif (key == "gpt41"):
                self.context.model = "gpt-4-0613"
                self.context.max_token = 4096
                print(f"Model = {self.context.model}")
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
            elif (key == "sample"):
                if (self.context.sample):
                    print(self.context.sample)
                    question = self.context.sample
                    return ("user", question)
            elif (key == "reset"):
                self.context = ChatContext(self.config)
            elif (key == "rpg1"):
                self.loadManifests('./rpg1')
                self.context = ChatContext(self.config)
            else:
                manifest = self.manifests.get(key)
                if (manifest):
                    self.context = ChatContext(self.config, role=key, manifest = manifest)
                    if not os.path.isdir(f"output/{self.context.role}"):
                        os.makedirs(f"output/{self.context.role}")
                    print(f"Activating: {self.context.title} (model={self.context.model}, temperature={self.context.temperature}, max_token={self.context.max_token})")

                    if (self.context.intro):
                        intro = self.context.intro[random.randrange(0, len(self.context.intro))]
                        self.context.messages.append({"role":"assistant", "content":intro})
                        print(f"\033[92m\033[1m{self.context.botName}\033[95m\033[0m: {intro}")
                else:            
                    print(f"Invalid slash command: {key}")
        else:
            return (roleInput, question)
        return (None, None)
    
    def start(self):
        chained = None
        name = None
        while not self.exit:
            if chained and name:
                # If there is any "chained" message, use it with the role "system"
                question = chained
                roleInput = "function"
                chained = None
                print(f"\033[95m\033[1mFunction: \033[95m\033[0m{question} for {name}")
            else:
                # Otherwise, retrieve the input from the user.
                question = input(f"\033[95m\033[1m{self.context.userName}: \033[95m\033[0m")
                roleInput = "user"
                name = None

            # Process slash commands (if exits)
            (role, question) = self.processSlash(roleInput, question)

            if role and question:
                self.context.appendQuestion(role, question, name)
                # Ask LLM to generate a response.
                (role, res, function_call) = self.context.generateResponse()

                if role and res:
                    print(f"\033[92m\033[1m{self.context.botName}\033[95m\033[0m: {res}")
                    self.context.messages.append({"role":role, "content":res})
                    with open(f"output/{self.context.role}/{self.context.time}.json", 'w') as f:
                        json.dump(self.context.messages, f)

                if (function_call):
                    arguments = function_call.get("arguments") 
                    if arguments and isinstance(arguments, str):
                        arguments = json.loads(arguments)      
                        function_call.arguments = arguments
                    print(colored(function_call, "blue"))
                    name = function_call.get("name")
                    if name:
                        action = self.context.actions.get(name)
                        if action:
                            template = action.get("template")
                            if template:
                                mime_type = action.get("mime_type") or ""
                                chained_msg = action.get("chained_msg") or f"{url}"
                                with open(f"{template}", 'r') as f:
                                    template = f.read()
                                    if self.context.verbose:
                                        print(template)
                                    ical = template.format(**arguments)
                                    url = f"data:{mime_type};charset=utf-8,{urllib.parse.quote_plus(ical)}"
                                    chained = chained_msg.format(url = url)
                        else:
                            function = self.context.module and self.context.module.get(name) or None
                            if function:
                                chained = function(**arguments)

config = ChatConfig()
print(config.ONELINE_HELP)
main = Main(config, "./prompts")
main.start()

