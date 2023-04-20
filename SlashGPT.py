#!/usr/bin/env python3
import os
import readline # So that input can handle Kanji & delete
import openai
from dotenv import load_dotenv
import json

# Configuration
load_dotenv() # Load default environment variables (.env)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
assert OPENAI_API_KEY, "OPENAI_API_KEY environment variable is missing from .env"
OPENAI_API_MODEL = os.getenv("OPENAI_API_MODEL", "gpt-3.5-turbo")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", 0.7))
print(f"Open AI Key = {OPENAI_API_KEY}")
print(f"Model = {OPENAI_API_MODEL}")
openai.api_key = OPENAI_API_KEY

# Reading Prompt files
prompts = {}
files = os.listdir("./prompts")
# print(files)
for file in files:
    key = file.split('.')[0]
    with open(f"./prompts/{file}", 'r') as f:
        data = json.load(f)
    # print(key, file, data)
    prompts[key] = data

print(prompts)
messages = []

while True:
    value = input("\033[95m\033[1mYou: \033[95m\033[0m")
    if (len(value) == 0):
        continue
    if (value[0] == "/"):
        key = value[1:]
        print(f"\033[92m\033[1m{key}\033[95m\033[0m")
        if (key == "bye"):
            break
        elif (key == "reset"):
            messages = []
            continue            
        else:
            prompt = prompts[key]
            if (prompt):
                print(prompt)
                messages = [{"role":"system", "content":'\n'.join(prompt["prompt"])}]
            else:            
                print(f"Invalid Slash command: {key}")
    else:  
        messages.append({"role":"user", "content":value})

    print(f"{messages}")

    response = openai.ChatCompletion.create(model=OPENAI_API_MODEL, messages=messages, temperature=OPENAI_TEMPERATURE)
    answer = response['choices'][0]['message']
    print(f"\033[92m\033[1mGPT\033[95m\033[0m: {answer['content']}")
    messages.append({"role":answer['role'], "content":answer['content']})
