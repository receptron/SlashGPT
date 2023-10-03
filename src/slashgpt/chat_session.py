import random
import re
import uuid
from typing import Optional

from slashgpt.chat_config import ChatConfig
from slashgpt.dbs.pinecone import DBPinecone
from slashgpt.history.base import ChatHistory
from slashgpt.history.storage.abstract import ChatHisoryAbstractStorage
from slashgpt.history.storage.memory import ChatHistoryMemoryStorage
from slashgpt.llms.default_config import default_llm_models
from slashgpt.llms.model import LlmModel, get_default_llm_model, get_llm_model_from_manifest
from slashgpt.manifest import Manifest
from slashgpt.utils.print import print_debug, print_error, print_warning


class ChatSession:
    """It represents a chat session with a particular AI agent."""

    def __init__(
        self,
        config: ChatConfig,
        default_llm_model: LlmModel = None,
        user_id: Optional[str] = None,
        history_engine: ChatHisoryAbstractStorage = None,
        manifest={},
        agent_name: str = "GPT",
        intro: bool = True,
        restore: bool = False,
    ):
        self.config = config
        """Configuration Object (ChatConfig), which specifies accessible LLM models"""
        self.agent_name = agent_name
        """Display name of the AI agent (str)"""
        self.manifest = Manifest(manifest if manifest else {}, config.base_path, agent_name)
        """Manifest which specifies the behavior of the AI agent (Manifest)"""
        self.user_id = user_id if user_id else str(uuid.uuid4())
        """Specified user id or randomly generated uuid (str)"""
        self.history = ChatHistory(history_engine or ChatHistoryMemoryStorage(self.user_id, agent_name))
        """Chat history (ChatHistory)"""

        # Load the model name and make it sure that we have required keys
        if self.manifest.model():
            llm_model = get_llm_model_from_manifest(self.manifest, self.config.llm_models)
        else:
            if default_llm_model:
                llm_model = default_llm_model
            else:
                llm_model = get_default_llm_model(default_llm_models)
        self.set_llm_model(llm_model)

        # Load the prompt, fill variables and append it as the system message
        self.prompt = self.manifest.prompt_data(config.manifests if hasattr(config, "manifests") else {})
        """Prompt for the AI agent (str)"""

        if self.prompt and not restore:
            self.append_message("system", self.prompt, True)

        # Prepare embedded database index
        self.vector_db = self.__get_vector_db()
        """Associated vector database (DBPinecone, optional, to be virtualized)"""

        # Load functions file if it is specified
        self.functions = self.manifest.functions()
        """List of function definitions (list, optional)"""
        if self.functions and self.config.verbose:
            print_debug(self.functions)

        self.intro_message = self.__set_intro(intro)
        """Introduction message (str, optional)"""

    def set_llm_model(self, llm_model: LlmModel):
        """Set the LLM model"""
        if llm_model.check_api_key():
            self.llm_model = llm_model
        else:
            print_error("You need to set " + llm_model.get("api_key") + " to use this model. ")
        if self.config.verbose:
            print_debug(f"Model = {self.llm_model.name()}")

    def __get_vector_db(self):
        # Todo: support other vector db
        embeddings = self.manifest.get("embeddings")
        if embeddings:
            table_name = embeddings.get("name")
            try:
                if embeddings["db_type"] == "pinecone":
                    return DBPinecone.factory(table_name, self.config.verbose)
            except Exception as e:
                print_warning(f"Pinecone Error: {e}")

    """
    Append a message to the chat session, specifying the role ("user", "system" or "function").
    In case of a function message, the name specifies the function name.
    """

    def append_message(self, role: str, message: str, preset: bool, name=None):
        """Append a message to the chat history
        Args:

            role (str): Either "user", "system" or "function"
            message (str): Message
            preset (bool): True, if it is preset by the manifest
            name (str, optional): function name (when the role is "function")
        """
        self.history.append_message(role, message, name, preset)

    def append_user_question(self, message: str):
        """Append a question from the user to the history
        and update the prompt if necessary (e.g, RAG)"""
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

    def __set_intro(self, use_intro: bool):
        intro_message = None
        intro = self.intro()
        if use_intro and intro:
            intro_message = intro[random.randrange(0, len(intro))]
            self.append_message("assistant", intro_message, True)
        return intro_message

    def call_llm(self):
        """
        Let the LLM generate a responce based on the messasges in this session.

        Returns:

            role: "assistent"
            res: message
            function_call: json representing the function call (optional)
        """
        messages = self.history.messages()
        (role, res, function_call) = self.llm_model.generate_response(messages, self.manifest, self.config.verbose)

        if role and res:
            self.append_message(role, res, False)

        return (res, function_call)

    def temperature(self):
        """Temperature specified in the manifest"""
        return self.manifest.temperature()

    def intro(self):
        """Introduction messages specified in the manifest"""
        return self.manifest.get("intro")

    def username(self):
        """User name specified in the manifest"""
        return self.manifest.username()

    def botname(self):
        """Bot name specified in the manifest"""
        return self.manifest.botname()

    def title(self):
        """Title of the AI agent specified in the manifest"""
        return self.manifest.title()
