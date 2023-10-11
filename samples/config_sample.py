import os
import sys

from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from config.llm_config_sample import llm_engine_configs, llm_models  # noqa: E402
from slashgpt.chat_app import ChatApplication
from slashgpt.chat_config_with_manifests import ChatConfigWithManifests  # noqa: E402
from slashgpt.chat_session import ChatSession  # noqa: E402
from slashgpt.function.jupyter_runtime import PythonRuntime  # noqa: E402
from slashgpt.history.storage.file import ChatHistoryFileStorage  # noqa: E402
from slashgpt.utils.print import print_error  # noqa: E402

load_dotenv()
current_dir = os.path.dirname(__file__)


class SampleApp:
    def __init__(self):
        self.config = config = ChatConfigWithManifests(current_dir, current_dir + "/manifests/sample", llm_models, llm_engine_configs)
        model = config.get_llm_model_from_key("gpt3")

        agent_name = "spacex"
        history_engine = ChatHistoryFileStorage("sample", agent_name)
        self.app = ChatApplication(
            config,
            self.callback,
            model=model,
            agent_name=agent_name,
            history_engine=history_engine,
            runtime=PythonRuntime(config.base_path + "/output/notebooks"),
        )

    def callback(self, callback_type, data):
        if callback_type == "function":
            (function_name, function_message) = data
            print(f"{function_name}: {function_message}")

    def main(self):
        question = "Who is the CEO of SpaceX?"
        self.app.session.append_user_question(question)
        self.app.process_llm()
        messages = self.app.session.context.messages()
        last_message = messages[len(messages) - 1]

        print(f"Q: {question}")
        print(f"A: {last_message.get('content')}")


app = SampleApp()
app.main()
