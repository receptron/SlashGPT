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

# Configuration
load_dotenv() # Load default environment variables (.env)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
assert OPENAI_API_KEY, "OPENAI_API_KEY environment variable is missing from .env"
OPENAI_API_MODEL = os.getenv("OPENAI_API_MODEL", "gpt-3.5-turbo-0613")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", 0.7))
GOOGLE_PALM_KEY = os.getenv("GOOGLE_PALM_KEY", None)
EMBEDDING_MODEL = "text-embedding-ada-002"
# print(f"Open AI Key = {OPENAI_API_KEY}")
print(f"Model = {OPENAI_API_MODEL}")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
# assert PINECONE_API_KEY, "PINECONE_API_KEY environment variable is missing from .env"
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "")
# assert (
#    PINECONE_ENVIRONMENT
#), "PINECONE_ENVIRONMENT environment variable is missing from .env"

# Initialize OpenAI and optinoally Pinecone and Palm 
openai.api_key = OPENAI_API_KEY
if (PINECONE_API_KEY and PINECONE_ENVIRONMENT):
    pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
if (GOOGLE_PALM_KEY):
    palm.configure(api_key=GOOGLE_PALM_KEY)

ONELINE_HELP = "System Slashes: /bye, /reset, /prompt, /sample, /gpt3, /gpt4, /palm, /verbose, /help"
print(ONELINE_HELP)

# Prepare output folders
if not os.path.isdir("output"):
    os.makedirs("output")
if not os.path.isdir("output/GPT"):
    os.makedirs("output/GPT")

# Read Manifest files

def loadManifests(folder: str = "./prompts"):
    results = {}
    files = os.listdir(folder)
    for file in files:
        key = file.split('.')[0]
        with open(f"{folder}/{file}", 'r') as f:
            data = json.load(f)
        # print(key, file, data)
        results[key] = data
    return results

manifests = loadManifests()

class ChatContext:
    def __init__(self, role: str = "GPT", manifest = None):
        self.role = role
        self.time = datetime.now()
        self.userName = "You"
        self.botName = "GPT"
        self.title = ""
        self.intro = None
        self.sample = None
        self.temperature = OPENAI_TEMPERATURE
        self.manifest = manifest
        self.prompt = None
        self.verbose = False
        self.index = None
        self.model = OPENAI_API_MODEL
        self.max_token = 4096
        self.translator = False
        self.messages = []
        self.functions = None
        self.template = None
        if (manifest):
            self.userName = manifest.get("you") or self.userName
            self.botName = manifest.get("bot") or context.role
            self.model = manifest.get("model") or self.model
            self.title = manifest.get("title")
            self.intro = manifest.get("intro")
            self.sample = manifest.get("sample") 
            self.translator = manifest.get("translator") or False
            if (manifest.get("temperature")):
                self.temperature = float(manifest.get("temperature"))
            self.prompt = '\n'.join(manifest["prompt"])
            if(re.search("\\{now\\}", self.prompt)):
                self.prompt = re.sub("\\{now\\}", self.time.isoformat(), self.prompt, 1)
            
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
                with open(f"./resources/{resource}", 'r') as f:
                    contents = f.read()
                    self.prompt = re.sub("\\{resource\\}", contents, self.prompt, 1)
            table_name = manifest.get("articles")
            if table_name and PINECONE_API_KEY and PINECONE_ENVIRONMENT:
                assert table_name in pinecone.list_indexes(), f"No Pinecone table named {table_name}"
                self.index = pinecone.Index(table_name)
            self.messages = [{"role":"system", "content":self.prompt}]
            functions = manifest.get("functions")
            if functions:
                with open(f"./resources/{functions}", 'r') as f:
                    self.functions = json.load(f)
                    if context.verbose:
                        print(self.functions)
            template = manifest.get("template")
            if template:
                with open(f"./resources/{template}", 'r') as f:
                    self.template = f.read()
                    if context.verbose:
                        print(self.template)

    def num_tokens(self, text: str) -> int:
        """Return the number of tokens in a string."""
        encoding = tiktoken.encoding_for_model(context.model)
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
            model=EMBEDDING_MODEL,
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
        if (context.verbose):
            print(f"Articles:{count}, Tokens:{self.num_tokens(articles + query)}")
        return articles

    def appendQuestion(self, question: str, role: str = "user"):
        print("role:", role)
        if self.translator:
            self.messages = [{
                "role": "system",
                "content":re.sub("\\{input\\}", question, self.prompt, 1)
            }]
        else:
            self.messages.append({"role":role, "content":question})
            if self.index:
                articles = self.fetch_related_articles(self.max_token - 500)
                assert self.messages[0]["role"] == "system", "Missing system message"
                self.messages[0] = {
                    "role":"system", 
                    "content":re.sub("\\{articles\\}", articles, self.prompt, 1)
                }

context = ChatContext()
chained = None

while True:
    roleInput = "user"
    if chained:
        question = chained
        roleInput = "system"
        print(f"\033[95m\033[1mSystem: \033[95m\033[0m{chained}")
    else:
        question = input(f"\033[95m\033[1m{context.userName}: \033[95m\033[0m")
    chained = None

    if (len(question) == 0):
        print(ONELINE_HELP)
        continue
    if (question[0] == "/"):
        key = question[1:]
        if (key == "help"):
            list = ", ".join(f"/{key}" for key in manifests.keys())
            print(f"Extensions: {list}")
            continue
        if (key == "bye"):
            break
        elif (key == "verbose"):
            context.verbose = context.verbose == False
            print(f"Verbose Mode: {context.verbose}")
            continue
        elif (key == "prompt"):
            if (len(context.messages) >= 1):
                print(context.messages[0].get("content"))
            continue
        elif (key == "gpt3"):
            context.model = "gpt-3.5-turbo-0613"
            context.max_token = 4096
            print(f"Model = {context.model}")
            continue
        elif (key == "gpt31"):
            context.model = "gpt-3.5-turbo-16k-0613"
            context.max_token = 4096 * 4
            print(f"Model = {context.model}")
            continue
        elif (key == "gpt4"):
            context.model = "gpt-4"
            context.max_token = 4096
            print(f"Model = {context.model}")
            continue
        elif (key == "gpt41"):
            context.model = "gpt-4-0613"
            context.max_token = 4096
            print(f"Model = {context.model}")
            continue
        elif (key == "palm"):
            if (GOOGLE_PALM_KEY):
                context.model = "palm"
                if (context.botName == "GPT"):
                    context.botName = "PaLM"
                print(f"Model = {context.model}")
            else:
                print("Error: Missing GOOGLE_PALM_KEY")
            continue
        elif (key == "palmt"):
            if (GOOGLE_PALM_KEY):
                context.model = "palmt"
                if (context.botName == "GPT"):
                    context.botName = "PaLM(Text)"
                print(f"Model = {context.model}")
            else:
                print("Error: Missing GOOGLE_PALM_KEY")
            continue
        elif (key == "sample"):
            if (context.sample):
                print(context.sample)
                question = context.sample
                context.appendQuestion(question)
            else:
                continue
        elif (key == "reset"):
            context = ChatContext()
            continue            
        elif (key == "rpg1"):
            manifests = loadManifests('./rpg1')
            context = ChatContext()
            continue            
        else:
            manifest = manifests.get(key)
            if (manifest):
                context = ChatContext(role=key, manifest = manifest)
                if not os.path.isdir(f"output/{context.role}"):
                    os.makedirs(f"output/{context.role}")
                print(f"Activating: {context.title} (model={context.model}, temperature={context.temperature})")

                if (context.intro):
                    intro = context.intro[random.randrange(0, len(context.intro))]
                    context.messages.append({"role":"assistant", "content":intro})
                    print(f"\033[92m\033[1m{context.botName}\033[95m\033[0m: {intro}")
                continue
            else:            
                print(f"Invalid slash command: {key}")
                continue
    else:
        context.appendQuestion(question, roleInput)

    # print(f"{messages}")
    if (context.model == "palm"):
        defaults = {
            'model': 'models/chat-bison-001',
            'temperature': context.temperature,
            'candidate_count': 1,
            'top_k': 40,
            'top_p': 0.95,
        }
        system = ""
        examples = []
        messages = []
        for message in context.messages:
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
    elif (context.model == "palmt"):
        defaults = {
            'model': 'models/text-bison-001',
            'temperature': context.temperature,
            'candidate_count': 1,
            'top_k': 40,
            'top_p': 0.95,
        }
        prompts = []
        for message in context.messages:
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
        if context.functions:
            response = openai.ChatCompletion.create(
                model=context.model,
                messages=context.messages,
                functions=context.functions,
                temperature=context.temperature)
        else:
            response = openai.ChatCompletion.create(
                model=context.model,
                messages=context.messages,
                temperature=context.temperature)
        if (context.verbose):
            print(f"model={response['model']}")
            print(f"usage={response['usage']}")
        answer = response['choices'][0]['message']
        res = answer['content']
        role = answer['role']
        function_call = answer.get('function_call')
        if (function_call):
            arguments = function_call.get("arguments") 
            if arguments and isinstance(arguments, str):
                function_call.arguments = json.loads(arguments)      
            print(colored(function_call, "blue"))
            name = function_call.get("name")
            if (name and name=="make_event"):
                chained = "The event was scheduled. Here is the invitation link: 'https://calendar.com/12345.ical'"
            else:
                # Reset the conversation to avoid confusion
                context.messages = context.messages[:1]

    if (res):
        print(f"\033[92m\033[1m{context.botName}\033[95m\033[0m: {res}")
        context.messages.append({"role":role, "content":res})
        with open(f"output/{context.role}/{context.time}.json", 'w') as f:
            json.dump(context.messages, f)
