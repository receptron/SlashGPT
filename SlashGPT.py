#!/usr/bin/env python3
import os
import readline # So that input can handle Kanji & delete
import openai
from dotenv import load_dotenv

# CONFIGURATIONS
load_dotenv() # Load default environment variables (.env)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
assert OPENAI_API_KEY, "OPENAI_API_KEY environment variable is missing from .env"
OPENAI_API_MODEL = os.getenv("OPENAI_API_MODEL", "gpt-3.5-turbo")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", 0.7))

print(f"Open AI Key = {OPENAI_API_KEY}")
print(f"Model = {OPENAI_API_MODEL}")

openai.api_key = OPENAI_API_KEY
messages = []

while True:
    value = input("\033[95m\033[1mYou: \033[95m\033[0m")
    if (len(value) == 0):
        break
    print(f"\033[92m\033[1m{value}\033[95m\033[0m")
    messages.append({"role":"user", "content":value})
    response = openai.ChatCompletion.create(model=OPENAI_API_MODEL, messages=messages, temperature=OPENAI_TEMPERATURE)
    answer = response['choices'][0]['message']
    print(f"\033[92m\033[1mGPT\033[95m\033[0m: {answer['content']}")
    messages.append({"role":answer['role'], "content":answer['content']})
