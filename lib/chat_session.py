import random
import re
import uuid

from termcolor import colored

from lib.chat_config import ChatConfig
from lib.dbs.pinecone import DBPinecone
from lib.history.base import ChatHistory
from lib.history.storage.memory import ChatHistoryMemoryStorage
from lib.llms.models import get_llm_model_from_manifest
from lib.manifest import Manifest
from lib.utils.utils import COLOR_DEBUG, COLOR_ERROR, COLOR_WARNING

"""
ChatSession represents a chat session with a particular AI agent.
The key is the identifier of the agent.
The manifest specifies behaviors of the agent.
"""


class ChatSession:
    def __init__(self, config: ChatConfig, manifest={}, manifest_key: str = "GPT"):
        self.config = config
        self.manifest_key = manifest_key

        self.manifest = Manifest(manifest if manifest else {}, manifest_key)

        self.userName = self.manifest.username()
        self.botName = self.manifest.botname()
        self.title = self.manifest.title()
        self.intro = self.manifest.get("intro")
        self.temperature = self.manifest.temperature()

        self.intro_message = None
        self.uid = str(uuid.uuid4())
        memory_history = ChatHistoryMemoryStorage(self.uid, manifest_key)
        self.history = ChatHistory(memory_history)

        # Load the model name and make it sure that we have required keys
        llm_model = get_llm_model_from_manifest(self.manifest)
        self.__set_llm_model(llm_model)

        # Load the prompt, fill variables and append it as the system message
        self.prompt = self.manifest.prompt_data(config.manifests)
        if self.prompt:
            self.append_message("system", self.prompt)

        # Prepare embedded database index
        self.vector_db = self.__get_vector_db()

        # Load functions file if it is specified
        self.functions = self.manifest.functions()
        if self.functions and self.config.verbose:
            print(colored(self.functions, COLOR_DEBUG))

    def __set_llm_model(self, llm_model):
        if llm_model.check_api_key(self.config):
            self.llm_model = llm_model
        else:
            print(
                colored(
                    "You need to set " + llm_model.get("api_key") + " to use this model. ",
                    COLOR_ERROR,
                )
            )
        if self.config.verbose:
            print(colored(f"Model = {self.llm_model.name()}", COLOR_DEBUG))

    def __get_vector_db(self):
        # Todo: support other vector dbs.
        embeddings = self.manifest.get("embeddings")
        if embeddings:
            table_name = embeddings.get("name")
            try:
                if embeddings["db_type"] == "pinecone":
                    return DBPinecone.factory(table_name, self.config)
            except Exception as e:
                print(colored(f"Pinecone Error: {e}", COLOR_WARNING))

    """
    Append a message to the chat session, specifying the role ("user", "system" or "function").
    In case of a function message, the name specifies the function name.
    """

    def append_message(self, role: str, message: str, name=None):
        self.history.append_message(role, message, name)

    def append_user_question(self, message: str):
        self.append_message("user", message)
        if self.vector_db:
            articles = self.vector_db.fetch_related_articles(self.llm_model.max_token() - 500)
            assert self.history.get_data(0, "role") == "system", "Missing system message"
            self.history.set(
                0,
                {
                    "role": "system",
                    "content": re.sub("\\{articles\\}", articles, self.prompt, 1),
                },
            )

    def set_intro(self):
        if self.intro:
            self.intro_message = self.intro[random.randrange(0, len(self.intro))]
            self.append_message("assistant", self.intro_message)

    """
    Let the LLM generate a responce based on the messasges in this session.
    Return values:
        role: "assistent"
        res: message
        function_call: json representing the function call (optional)
    """

    def call_llm(self):
        (role, res, function_call) = self.llm_model.generate_response(self.history.messages(), self.manifest, self.config.verbose)

        if role and res:
            self.append_message(role, res)

        return (res, function_call)
