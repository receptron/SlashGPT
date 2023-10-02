import json
import os
import re
import sys

from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))
sys.path.append(os.path.join(os.path.dirname(__file__), "../sample"))

from config.llm_config_sample import llm_engine_configs, llm_models  # noqa: E402
from slashgpt.chat_session import ChatSession  # noqa: E402
from slashgpt.chat_slash_config import ChatSlashConfig  # noqa: E402
from slashgpt.function.jupyter_runtime import PythonRuntime  # noqa: E402
from slashgpt.history.storage.file import ChatHistoryFileStorage  # noqa: E402
from slashgpt.llms.model import get_llm_model_from_key  # noqa: E402
from slashgpt.utils.print import print_error  # noqa: E402

load_dotenv()
current_dir = os.path.dirname(__file__)
runtime = PythonRuntime(current_dir + "/output/notebooks")

def process_llm(session):
    try:
        (res, function_call) = session.call_llm()

        if function_call:
            runtime.create_notebook(session.llm_model.name())
            (
                function_message,
                function_name,
                should_call_llm,
            ) = function_call.process_function_call(
                session.history,
                runtime,
                True,
            )
            if should_call_llm:
                process_llm(session)

    except Exception as e:
        print_error(f"Exception: Restarting the chat :{e}")

config = ChatSlashConfig(current_dir, current_dir + "/manifests/sample", llm_models, llm_engine_configs)
agent_name = "spacex"
llm_name = "gpt3"
question = "Who is the CEO of SpaceX?"
manifest = config.manifests[agent_name]

engine = ChatHistoryFileStorage("sample", agent_name)
# session_id = engine.session_id

session = ChatSession(config, manifest=manifest, agent_name=agent_name, history_engine=engine)

model = get_llm_model_from_key(llm_name, config.llm_models)
session.set_llm_model(model)
session.append_user_question(session.manifest.format_question(question))
process_llm(session)
messages = engine.messages()
last_message = messages[len(messages)-1]

print(f"Q: {question}")
print(f"A: {last_message.get('content')}")