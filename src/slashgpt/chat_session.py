import random
import re
import uuid
from typing import Optional

from termcolor import colored

from slashgpt.chat_config import ChatConfig
from slashgpt.dbs.pinecone import DBPinecone
from slashgpt.history.base import ChatHistory
from slashgpt.history.storage.memory import ChatHistoryMemoryStorage
from slashgpt.llms.default_config import default_llm_engine_configs, default_llm_models
from slashgpt.llms.engine_factory import LLMEngineFactory
from slashgpt.llms.model import LlmModel, get_llm_model_from_manifest
from slashgpt.manifest import Manifest
from slashgpt.utils.utils import COLOR_DEBUG, COLOR_ERROR, COLOR_WARNING

"""
ChatSession represents a chat session with a particular AI agent.
The key is the identifier of the agent.
The manifest specifies behaviors of the agent.
"""


class ChatSession:
    def __init__(
        self,
        config: ChatConfig,
        user_id: Optional[str] = None,
        history_engine=ChatHistoryMemoryStorage,
        manifest={},
        agent_name: str = "GPT",
        intro: bool = True,
    ):
        self.config = config
        self.agent_name = agent_name

        self.manifest = Manifest(manifest if manifest else {}, config.base_path, agent_name)

        self.userName = self.manifest.username()
        self.botName = self.manifest.botname()
        self.title = self.manifest.title()
        self.intro = self.manifest.get("intro")
        self.temperature = self.manifest.temperature()

        self.intro_message = None
        self.user_id = user_id if user_id else str(uuid.uuid4())
        memory_history = history_engine(self.user_id, agent_name)
        self.history = ChatHistory(memory_history)

        # llm
        if not self.config.llm_models:
            self.config.llm_models = default_llm_models
        if not self.config.llm_engine_configs:
            self.config.llm_engine_configs = default_llm_engine_configs

        # engine
        if self.config.llm_engine_configs:
            LLMEngineFactory.llm_engine_configs = self.config.llm_engine_configs

        # Load the model name and make it sure that we have required keys
        llm_model = get_llm_model_from_manifest(self.manifest, self.config.llm_models)
        self.set_llm_model(llm_model)

        # Load the prompt, fill variables and append it as the system message
        self.prompt = self.manifest.prompt_data(config.manifests if hasattr(config, "manifests") else {})
        if self.prompt:
            self.append_message("system", self.prompt, True)

        # Prepare embedded database index
        self.vector_db = self.__get_vector_db()

        # Load functions file if it is specified
        self.functions = self.manifest.functions()
        if self.functions and self.config.verbose:
            print(colored(self.functions, COLOR_DEBUG))

        if intro:
            self.set_intro()

    def set_llm_model(self, llm_model: LlmModel):
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

    def append_message(self, role: str, message: str, preset: bool, name=None):
        self.history.append_message(role, message, name, preset)

    def append_user_question(self, message: str):
        self.append_message("user", message, False)
        if self.vector_db:
            articles = self.vector_db.fetch_related_articles(self.history.messages(), self.llm_model.name(), self.llm_model.max_token() - 500)
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
            self.append_message("assistant", self.intro_message, True)

    """
    Let the LLM generate a responce based on the messasges in this session.
    Return values:
        role: "assistent"
        res: message
        function_call: json representing the function call (optional)
    """

    def call_llm(self):
        messages = self.history.messages()
        (role, res, function_call) = self.llm_model.generate_response(messages, self.manifest, self.config.verbose)

        if role and res:
            self.append_message(role, res, False)

        return (res, function_call)
