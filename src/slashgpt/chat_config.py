import os
from typing import Optional

import google.generativeai as palm
import openai
import pinecone
from dotenv import load_dotenv

"""
ChatConfig is a singleton, which holds global states, including various secret keys
"""


class ChatConfig:
    def __init__(self, base_path: str, llm_models: Optional[dict] = None, llm_engine_configs: Optional[dict] = None):
        self.base_path = base_path
        # Load various keys from .env file
        load_dotenv()
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        assert self.OPENAI_API_KEY, "OPENAI_API_KEY environment variable is missing from .env"
        self.GOOGLE_PALM_KEY = os.getenv("GOOGLE_PALM_KEY", None)
        self.EMBEDDING_MODEL = "text-embedding-ada-002"
        self.PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
        self.PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "")
        self.REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", None)

        self.verbose = False

        # Initialize OpenAI and optinoally Pinecone and Palm
        openai.api_key = self.OPENAI_API_KEY
        if self.PINECONE_API_KEY and self.PINECONE_ENVIRONMENT:
            pinecone.init(api_key=self.PINECONE_API_KEY, environment=self.PINECONE_ENVIRONMENT)
        if self.GOOGLE_PALM_KEY:
            palm.configure(api_key=self.GOOGLE_PALM_KEY)

        self.llm_models = llm_models
        self.llm_engine_configs = llm_engine_configs

    # for llm
    def has_value_for_key(self, key: str):
        if key == "REPLICATE_API_TOKEN":
            return self.REPLICATE_API_TOKEN is not None
        if key == "GOOGLE_PALM_KEY":
            return self.GOOGLE_PALM_KEY is not None
        return False
