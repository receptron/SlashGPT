#!/usr/bin/env python3
import os
import openai
from dotenv import load_dotenv

# CONFIGURATIONS
load_dotenv() # Load default environment variables (.env)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
assert OPENAI_API_KEY, "OPENAI_API_KEY environment variable is missing from .env"

print(f"Open AI Key = {OPENAI_API_KEY}")