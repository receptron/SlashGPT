from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from slashgpt.chat_session import ChatSession
from slashgpt.utils.print import print_error, print_warning

if TYPE_CHECKING:
    from slashgpt.chat_config_with_manifests import ChatConfigWithManifests
    from slashgpt.function.jupyter_runtime import PythonRuntime
    from slashgpt.history.storage.abstract import ChatHistoryAbstractStorage
    from slashgpt.llms.model import LlmModel


class ChatApplication:
    """This instance represents an LLM application,
    which consists of multiple LLM agents specified by the manifests of the ChatConfigWithManifests instance."""

    def __init__(self, config: ChatConfigWithManifests, callback=None, model: Optional[LlmModel] = None, runtime: Optional[PythonRuntime] = None):
        self.config: ChatConfigWithManifests = config
        """The configuration of LLMs and manifests """
        self.llm_model: LlmModel = model or self.config.get_default_llm_model()
        """The default LLM model for this application"""
        self.runtime: Optional[PythonRuntime] = runtime
        """Python runtime"""
        self._callback = callback or self._noop
        """Callback function"""
        self.session: Optional[ChatSession] = None
        """Active session, initially None"""

    def switch_session(
        self,
        agent_name: Optional[str] = None,
        intro: bool = True,
        memory: Optional[dict] = None,
        merge_memory: bool = False,
        history_engine: Optional[ChatHistoryAbstractStorage] = None,
    ):
        """
        It terminates the current chat session (if any) and start a new.

            agent_name(str): specifies the AI agent to activate
            intro(bool): specifies if it needs to add the introduction message
            memory(dict, optional): initial set of short-term memory
            merge_memory(bool): if True, the memory is merged with the existing memory
            history_engine(ChatHistoryAbstractStorage, optional): history_engine
        """
        if agent_name is not None:
            if self.config.has_manifest(agent_name):
                manifest = self.config.manifests.get(agent_name)
                if merge_memory and self.session and self.session.memory:
                    merged_memory = self.session.memory.copy()
                    merged_memory.update(memory or {})
                    memory = merged_memory
                self.session = ChatSession(
                    self.config,
                    default_llm_model=self.llm_model,
                    manifest=manifest,
                    agent_name=agent_name,
                    intro=intro,
                    memory=memory,
                    history_engine=history_engine,
                )
                if self.config.verbose:
                    self._callback(
                        "info",
                        f"Activating: {self.session.title()} (model={self.session.llm_model.name()}, temperature={self.session.temperature()}, max_token={self.session.llm_model.max_token()})",
                    )
                else:
                    self._callback("info", f"Activating: {self.session.title()}")
                if self.session.manifest.get("notebook") and self.runtime:
                    (result, _) = self.runtime.create_notebook(self.session.llm_model.name())
                    self._callback("info", f"Created a notebook: {result.get('notebook_name')}")

                if self.session.intro_message:
                    self._callback("bot", self.session.intro_message)
                return
            else:
                print_error(f"Invalid slash command: {agent_name}")

        print_warning("No agent_name was spacified")
        self.session = ChatSession(self.config, default_llm_model=self.llm_model, history_engine=history_engine)

    def _noop(self, callback_type, data):
        pass

    def _process_event(self, callback_type, data):
        self._callback(callback_type, data)

        if callback_type == "emit":
            # All emit methods must be processed here
            (action_method, action_data) = data

            if action_method == "switch_session":
                memory = action_data.get("memory")

                agent_to_activate = action_data.get("agent")
                if agent_to_activate:
                    merge_memory = action_data.get("merge")
                    self.switch_session(agent_name=agent_to_activate, memory=memory, merge_memory=merge_memory)
                    message_to_append = action_data.get("message")
                    if message_to_append:
                        self.session.append_user_question(message_to_append)
                        self.process_llm()
                    elif action_data.get("initiate"):
                        self.process_llm()

    def process_llm(self):
        """It calls the LLM with the current context (system prompt and messages)
        and process the response (such as function call)"""
        try:
            self.session.call_loop(self._process_event, self.runtime)
        except Exception as e:
            print_error(f"Exception: Restarting the chat :{e}")
            self.switch_session(self.session.agent_name)
            if self.config.verbose:
                raise
