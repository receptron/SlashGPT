from typing import Optional

from slashgpt.chat_config_with_manifests import ChatConfigWithManifests
from slashgpt.chat_session import ChatSession
from slashgpt.function.jupyter_runtime import PythonRuntime
from slashgpt.utils.print import print_error, print_info


class ChatApplication:
    def __init__(self, config: ChatConfigWithManifests):
        self.config = config
        self.llm_model = self.config.get_default_llm_model()
        self.session = ChatSession(self.config, default_llm_model=self.llm_model)
        self.runtime = PythonRuntime(self.config.base_path + "/output/notebooks")
        self._callback = self._process_event

    """
    switchSession terminate the current chat session and start a new.
    The key specifies the AI agent.
    """

    def switch_session(self, agent_name: str, intro: bool = True, memory: Optional[dict] = None):
        if agent_name is None:
            self.session = ChatSession(self.config, default_llm_model=self.llm_model)
            return

        if self.config.has_manifest(agent_name):
            manifest = self.config.manifests.get(agent_name)
            self.session = ChatSession(
                self.config, default_llm_model=self.llm_model, manifest=manifest, agent_name=agent_name, intro=intro, memory=memory
            )
            if self.config.verbose:
                print_info(
                    f"Activating: {self.session.title()} (model={self.session.llm_model.name()}, temperature={self.session.temperature()}, max_token={self.session.llm_model.max_token()})"
                )
            else:
                print_info(f"Activating: {self.session.title()}")
            if self.session.manifest.get("notebook"):
                (result, _) = self.runtime.create_notebook(self.session.llm_model.name())
                print_info(f"Created a notebook: {result.get('notebook_name')}")

            if self.session.intro_message:
                self._callback("bot", self.session.intro_message)
        else:
            print_error(f"Invalid slash command: {agent_name}")

    def set_callback(self, callback):
        prev_callback = self._callback
        self._callback = callback
        return prev_callback

    def _process_event(self, callback_type, data):
        if callback_type == "emit":
            # All emit methods must be processed here
            (action_method, action_data) = data

            if action_method == "switch_session":
                memory = action_data.get("memory")
                if memory is not None:
                    self.session.context.setMemory(memory, action_data.get("merge"))

                agent_to_activate = action_data.get("agent")
                if agent_to_activate:
                    self.switch_session(agent_to_activate, memory=self.session.context.memory())
                    message_to_append = action_data.get("message")
                    if message_to_append:
                        self.session.append_user_question(message_to_append)
                    self.process_llm()

    def process_llm(self):
        try:
            self.session.call_loop(self._callback, self.config.verbose, self.runtime)
        except Exception as e:
            print_error(f"Exception: Restarting the chat :{e}")
            self.switch_session(self.session.agent_name)
            if self.config.verbose:
                raise
