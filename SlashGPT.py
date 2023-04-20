#!/usr/bin/env python3
import os
import readline # So that input can handle Kanji & delete
import openai
from dotenv import load_dotenv

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
files = os.listdir("./prompts")
print(files)

messages = []

while True:
    value = input("\033[95m\033[1mYou: \033[95m\033[0m")
    if (len(value) == 0):
        continue
    if (value[0] == "/"):
        print(f"\033[92m\033[1m{value}\033[95m\033[0m")
        if (value == "/bye"):
            break
        elif (value == "/reset"):
            messages = []
            continue            
        elif (value == "/patent"):
            messages = [{"role":"system", "content":"""
                You are a patent attoney, who is responsible in 
                (1) getting novel ideas from the client,
                (2) identify patentable ideas,
                (3) discuss those ideas with the client in plain English,
                (4) prepare a summary document in plain English, from which another attoney will generate the patent application.
            """}]
        elif (value == "/english"):
            messages = [{"role":"system", "content":"""
                You are a English teacher. 
                First, always ask the native language of the student simply asking "What is your native language?", and switch the discussion to that language.
                Second, ask for the target TOEIC level.
            """}]
        elif (value == "/therapy"):
            messages = [{"role":"system", "content":"""
                You are a therapist. Ask various questions and listen.
            """}]
        else:
            print("Invalid Slash command")
    else:  
        messages.append({"role":"user", "content":value})

    # print(f"{messages}")
    response = openai.ChatCompletion.create(model=OPENAI_API_MODEL, messages=messages, temperature=OPENAI_TEMPERATURE)
    answer = response['choices'][0]['message']
    print(f"\033[92m\033[1mGPT\033[95m\033[0m: {answer['content']}")
    messages.append({"role":answer['role'], "content":answer['content']})
