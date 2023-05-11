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

# Configuration
load_dotenv() # Load default environment variables (.env)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
assert OPENAI_API_KEY, "OPENAI_API_KEY environment variable is missing from .env"
OPENAI_API_MODEL = os.getenv("OPENAI_API_MODEL", "gpt-3.5-turbo")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", 0.7))
EMBEDDING_MODEL = "text-embedding-ada-002"
# print(f"Open AI Key = {OPENAI_API_KEY}")
print(f"Model = {OPENAI_API_MODEL}")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
assert PINECONE_API_KEY, "PINECONE_API_KEY environment variable is missing from .env"
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "")
assert (
    PINECONE_ENVIRONMENT
), "PINECONE_ENVIRONMENT environment variable is missing from .env"

# Initialize Pinecone & OpenAI
pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
openai.api_key = OPENAI_API_KEY

oneline_help = "System Slashes: /bye, /reset, /help, /prompt, /gpt3, /gpt4"
print(oneline_help)

# Reading Prompt files
prompts = {}
files = os.listdir("./prompts")

if not os.path.isdir("output"):
    os.makedirs("output")
if not os.path.isdir("output/GPT"):
    os.makedirs("output/GPT")

# print(files)
for file in files:
    key = file.split('.')[0]
    with open(f"./prompts/{file}", 'r') as f:
        data = json.load(f)
    # print(key, file, data)
    prompts[key] = data

messages = []
context = "GPT"
context_time = datetime.now()
userName = "You"
botName = "GPT"
temperature = OPENAI_TEMPERATURE
prompt = None
index = None
contents = ""

def strings_ranked_by_relatedness(
    query: str,
    index: pinecone.Index,
    top_n: int = 100
) -> object:
    """Returns a list of strings and relatednesses, sorted from most related to least."""
    query_embedding_response = openai.Embedding.create(
        model=EMBEDDING_MODEL,
        input=query,
    )
    query_embedding = query_embedding_response["data"][0]["embedding"]

    results = index.query(query_embedding, top_k=top_n, include_metadata=True)
    return results

def num_tokens(text: str) -> int:
    """Return the number of tokens in a string."""
    encoding = tiktoken.encoding_for_model(OPENAI_API_MODEL)
    return len(encoding.encode(text))

def query_message(
    query: str,
    index: pinecone.Index,
    token_budget: int
) -> str:
    """Return a message for GPT, with relevant source texts pulled from a dataframe."""
    results = strings_ranked_by_relatedness(query, index)
    message = ""
    for match in results["matches"]:
        string = match["metadata"]["text"]
        next_article = f'\n\nWikipedia article section:\n"""\n{string}\n"""'
        if (
            num_tokens(message + next_article + query)
            > token_budget
        ):
            break
        else:
            message += next_article
    return message

while True:
    question = input(f"\033[95m\033[1m{userName}: \033[95m\033[0m")
    if (len(question) == 0):
        print(oneline_help)
        continue
    if (question[0] == "/"):
        key = question[1:]
        if (key == "help"):
            list = ", ".join(f"/{key}" for key in prompts.keys())
            print(f"Extensions: {list}")
            continue
        if (key == "bye"):
            break
        elif (key == "prompt"):
            if (len(messages) >= 1 and messages[0].get("role")=="system"):
                print(messages[0].get("content"))
            elif (index):
                print(contents)
            continue
        elif (key == "gpt3"):
            OPENAI_API_MODEL = "gpt-3.5-turbo"
            print(f"Model = {OPENAI_API_MODEL}")
            continue
        elif (key == "gpt4"):
            OPENAI_API_MODEL = "gpt-4"
            print(f"Model = {OPENAI_API_MODEL}")
            continue
        elif (key == "sample" and prompt != None):
            question = prompt.get("sample") 
            if (question):
                if index:
                    articles = query_message(question, index, 4096 - 500)
                    messages = [{"role":"system", "content":re.sub("\\{articles\\}", articles, contents, 1)}]
                print(question)
                messages.append({"role":"user", "content":question})
            else:
                continue
        elif (key == "reset"):
            messages = []
            context = "GPT"
            context_time = datetime.now()
            userName = "You"
            botName = "GPT"
            temperature = OPENAI_TEMPERATURE
            OPENAI_API_MODEL = "gpt-3.5-turbo"
            prompt = None
            index = None
            continue            
        else:
            prompt = prompts.get(key)
            if (prompt):
                context = key
                context_time = datetime.now()
                if not os.path.isdir(f"output/{context}"):
                    os.makedirs(f"output/{context}")
                title = prompt["title"]
                temperature = OPENAI_TEMPERATURE
                if (prompt.get("temperature")):
                    temperature = float(prompt.get("temperature"))
                if (prompt.get("model")):
                    OPENAI_API_MODEL = prompt.get("model")
                else:
                    OPENAI_API_MODEL = "gpt-3.5-turbo"
                print(f"Activating: {title} (model={OPENAI_API_MODEL}, temperature={temperature})")
                userName = prompt.get("you") or "You"
                botName = prompt.get("bot") or context
                contents = '\n'.join(prompt["prompt"])
                data = prompt.get("data")
                if data:
                    # Shuffle 
                    for i in range(len(data)):
                        j = random.randrange(0, len(data))
                        temp = data[i]
                        data[i] = data[j]
                        data[j] = temp
                    j = 0
                    while(re.search("\\{random\\}", contents)):
                        contents = re.sub("\\{random\\}", data[j], contents, 1)
                        j += 1

                table_name = prompt.get("articles")
                if table_name:
                    assert table_name in pinecone.list_indexes(), f"No Pinecone table named {table_name}"
                    index = pinecone.Index(table_name)
                    print(index)
                    messages = []
                else:
                    index = None
                    messages = [{"role":"system", "content":contents}]

                intros = prompt.get("intro") 
                if (intros):
                    intro = intros[random.randrange(0, len(intros))]
                    messages.append({"role":"assistant", "content":intro})
                continue
            else:            
                print(f"Invalid slash command: {key}")
                continue
    else:  
        if index:
            articles = query_message(question, index, 4096 - 500)
            messages = [{"role":"system", "content":re.sub("\\{articles\\}", articles, contents, 1)}]
        messages.append({"role":"user", "content":question})

    # print(f"{messages}")

    response = openai.ChatCompletion.create(model=OPENAI_API_MODEL, messages=messages, temperature=temperature)
    answer = response['choices'][0]['message']
    res = answer['content']
    print(f"\033[92m\033[1m{botName}\033[95m\033[0m: {res}")

    messages.append({"role":answer['role'], "content":res})
    with open(f"output/{context}/{context_time}.json", 'w') as f:
        json.dump(messages, f)
