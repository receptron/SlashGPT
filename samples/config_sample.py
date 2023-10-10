import os
import sys

from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from config.llm_config_sample import llm_engine_configs, llm_models  # noqa: E402
from slashgpt.chat_config_with_manifests import ChatConfigWithManifests  # noqa: E402
from slashgpt.chat_session import ChatSession  # noqa: E402
from slashgpt.function.jupyter_runtime import PythonRuntime  # noqa: E402
from slashgpt.history.storage.file import ChatHistoryFileStorage  # noqa: E402
from slashgpt.utils.print import print_error  # noqa: E402

load_dotenv()
current_dir = os.path.dirname(__file__)


class SampleApp:
    def __init__(self):
        agent_name = "spacex"
        self.config = config = ChatConfigWithManifests(current_dir, current_dir + "/manifests/sample", llm_models, llm_engine_configs)
        self.runtime = PythonRuntime(current_dir + "/output/notebooks")
        history_engine = ChatHistoryFileStorage("sample", agent_name)
        # session_id = engine.session_id
        model = config.get_llm_model_from_key("gpt3")
        manifest = config.manifests[agent_name]
        self.session = ChatSession(config, default_llm_model=model, manifest=manifest, agent_name=agent_name, history_engine=history_engine)

    def callback(self, callback_type, data):
        if callback_type == "emit":
            (action_method, action_data) = data
            # All emit methods must be processed here
            if action_method == "switch_session":
                self.switch_session(action_data.get("manifest"), intro=False)
                self.query_llm(action_data.get("message"))
        if callback_type == "function":
            (function_name, function_message) = data
            print(f"{function_name}: {function_message}")

    def process_llm(self):
        try:
            self.session.call_loop(self.callback, self.config.verbose, self.runtime)

        except Exception as e:
            print_error(f"Exception: Restarting the chat :{e}")

    def main(self):
        question = "Who is the CEO of SpaceX?"
        self.session.append_user_question(self.session.manifest.format_question(question))
        self.process_llm()
        messages = self.session.context.messages()
        last_message = messages[len(messages) - 1]

        print(f"Q: {question}")
        print(f"A: {last_message.get('content')}")


app = SampleApp()
app.main()
