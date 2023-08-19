from dotenv import load_dotenv
import os
import json
import openai
import pinecone
import google.generativeai as palm

LONG_HELP = """
/switch root:      Start from the scratch (going back to dispatcher)
/switch roles1:    Switch the manifest set to ones in prompts (original)
/switch roles2:    Switch the manifest set to ones in roles2
/bye:       Terminate the app
/new:       Start a new chat session
/prompt:    Display the current prompt
/history:   Display the chat history
/sample:    Make the sample request
/llm gpt3:      Switch the model to gpt-3.5-turbo-0613
/llm gpt31:     Switch the model to gpt-3.5-turbo-16k-0613
/llm gpt4:      Switch the model to gpt-4-0613
/llm palm:      Switch the model to Google PaLM
/llm llama2:    Switch the model to LlaMA2 7b
/llm llama270:  Switch the model to LlaMA2 70b
/llm vicuna:    Switch the model to Vicuna 16b
/verbose:   Toggle verbose switch
"""

"""
ChatConfig is a singleton, which holds global states, including various secret keys and the list of manifests.
"""
class ChatConfig:
    def __init__(self, pathManifests):
        # Load various keys from .env file
        load_dotenv() 
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        assert self.OPENAI_API_KEY, "OPENAI_API_KEY environment variable is missing from .env"
        self.GOOGLE_PALM_KEY = os.getenv("GOOGLE_PALM_KEY", None)
        self.EMBEDDING_MODEL = "text-embedding-ada-002"
        self.PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
        self.PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "")
        self.REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", None)

        # Initialize other settings and load all manifests
        self.verbose = False
        self.audio = None
        self.ONELINE_HELP = "System Slashes: /bye, /new, /prompt, /sample, /help, ..."
        self.LONG_HELP = LONG_HELP
        self.load_manifests(pathManifests)

        # Initialize OpenAI and optinoally Pinecone and Palm 
        openai.api_key = self.OPENAI_API_KEY
        if self.PINECONE_API_KEY and self.PINECONE_ENVIRONMENT:
            pinecone.init(api_key=self.PINECONE_API_KEY, environment=self.PINECONE_ENVIRONMENT)
        if self.GOOGLE_PALM_KEY:
            palm.configure(api_key=self.GOOGLE_PALM_KEY)

    """
    Load a set of manifests. 
    It's called initially, but it's called also when the user makes a request to switch the set (such as roles1).
    """
    def load_manifests(self, path):
        self.manifests = {}
        files = os.listdir(path)
        for file in files:
            with open(f"{path}/{file}", 'r',encoding="utf-8") as f:	# encoding add for Win
                self.manifests[file.split('.')[0]] = json.load(f)


    def has_value_for_key(self, key):
        if key == "REPLICATE_API_TOKEN":
            return self.REPLICATE_API_TOKEN != None
        if key == "GOOGLE_PALM_KEY":
            return self.GOOGLE_PALM_KEY != None
        return False

    def has_manifest(self, key):
        return key in self.manifests
