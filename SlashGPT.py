#!/usr/bin/env python3
import os
import readline # So that input can handle Kanji & delete
import openai
from dotenv import load_dotenv
import json
from datetime import datetime
import re
import random

# Configuration
load_dotenv() # Load default environment variables (.env)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
assert OPENAI_API_KEY, "OPENAI_API_KEY environment variable is missing from .env"
OPENAI_API_MODEL = os.getenv("OPENAI_API_MODEL", "gpt-3.5-turbo")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", 0.7))
# print(f"Open AI Key = {OPENAI_API_KEY}")
print(f"Model = {OPENAI_API_MODEL}")
oneline_help = "System Slashes: /bye, /reset, /help, /prompt, /gpt3, /gpt4"
print(oneline_help)
openai.api_key = OPENAI_API_KEY

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

while True:
    value = input(f"\033[95m\033[1m{userName}: \033[95m\033[0m")
    if (len(value) == 0):
        print(oneline_help)
        continue
    if (value[0] == "/"):
        key = value[1:]
        if (key == "help"):
            list = ", ".join(f"/{key}" for key in prompts.keys())
            print(f"Extensions: {list}")
            continue
        if (key == "bye"):
            break
        elif (key == "prompt"):
            if (len(messages) >= 1 and messages[0].get("role")=="system"):
                print(messages[0].get("content"))
            continue
        elif (key == "gpt3"):
            OPENAI_API_MODEL = "gpt-3.5-turbo"
            print(f"Model = {OPENAI_API_MODEL}")
            continue
        elif (key == "gpt4"):
            OPENAI_API_MODEL = "gpt-4"
            print(f"Model = {OPENAI_API_MODEL}")
            continue
        elif (key == "reset"):
            messages = []
            context = "GPT"
            context_time = datetime.now()
            userName = "You"
            botName = "GPT"
            temperature = OPENAI_TEMPERATURE
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
                print(f"Activating: {title} (model={OPENAI_API_MODEL}, temperature={temperature})")
                userName = prompt.get("you") or "You"
                botName = prompt.get("bot") or context
                contents = '\n'.join(prompt["prompt"])
                data = prompt.get("data")
                if data:
                    # Shuffle 
                    for i in range(len(data)):
                        index = random.randrange(0, len(data))
                        temp = data[i]
                        data[i] = data[index]
                        data[index] = temp
                    index = 0
                    while(re.search("\\{random\\}", contents)):
                        contents = re.sub("\\{random\\}", data[index], contents, 1)
                        index += 1
                messages = [{"role":"system", "content":contents}]
                continue
            else:            
                print(f"Invalid slash command: {key}")
                continue
    else:  
        messages.append({"role":"user", "content":value})

    # print(f"{messages}")

    response = openai.ChatCompletion.create(model=OPENAI_API_MODEL, messages=messages, temperature=temperature)
    answer = response['choices'][0]['message']
    print(f"\033[92m\033[1m{botName}\033[95m\033[0m: {answer['content']}")
    messages.append({"role":answer['role'], "content":answer['content']})
    with open(f"output/{context}/{context_time}.json", 'w') as f:
        json.dump(messages, f)
