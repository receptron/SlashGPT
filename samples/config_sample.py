import os
import sys

from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from config.llm_config_sample import llm_engine_configs, llm_models  # noqa: E402
from slashgpt import ChatApplication  # noqa: E402
from slashgpt import ChatConfigWithManifests  # noqa: E402
from slashgpt import ChatHistoryFileStorage  # noqa: E402
from slashgpt import PythonRuntime  # noqa: E402

load_dotenv()
current_dir = os.path.dirname(__file__)


class SampleApp:
    def __init__(self):
        self.config = config = ChatConfigWithManifests(current_dir, current_dir + "/manifests/sample", llm_models, llm_engine_configs)
        model = config.get_llm_model_from_key("gpt3")

        self.app = ChatApplication(
            config,
            self.callback,
            model=model,
            runtime=PythonRuntime(config.base_path + "/output/notebooks"),
        )

        agent_name = "spacex"
        history_engine = ChatHistoryFileStorage("sample", agent_name)
        self.app.switch_session(agent_name=agent_name, history_engine=history_engine)

    def callback(self, callback_type, data):
        if callback_type == "bot":
            print(f"A: {data}")
        if callback_type == "info":
            print(data)
        if callback_type == "function":
            (function_name, function_message) = data
            print(f"{function_name}: {function_message}")

    def main(self):
        question = "Who is the CEO of SpaceX?"
        print(f"Q: {question}")
        self.app.session.append_user_question(question)
        self.app.process_llm()


app = SampleApp()
app.main()
