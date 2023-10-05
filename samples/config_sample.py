import os
import sys

from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from config.llm_config_sample import llm_engine_configs, llm_models  # noqa: E402
from slashgpt.chat_config_with_manifests import ChatConfigWithManifests  # noqa: E402
from slashgpt.chat_session import ChatSession  # noqa: E402
from slashgpt.function.jupyter_runtime import PythonRuntime  # noqa: E402
from slashgpt.history.storage.file import ChatHistoryFileStorage  # noqa: E402
from slashgpt.llms.model import LlmModel  # noqa: E402
from slashgpt.utils.print import print_error  # noqa: E402

load_dotenv()
current_dir = os.path.dirname(__file__)
runtime = PythonRuntime(current_dir + "/output/notebooks")
config = ChatConfigWithManifests(current_dir, current_dir + "/manifests/sample", llm_models, llm_engine_configs)


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


def create_session(agent_name: str, llm_name: str):
    manifest = config.manifests[agent_name]
    history = ChatHistoryFileStorage("sample", agent_name)
    # session_id = engine.session_id
    model = LlmModel.get_llm_model_from_key(llm_name, config)
    session = ChatSession(config, default_llm_model=model, manifest=manifest, agent_name=agent_name, history_engine=history)
    return (session, history)


def main():
    (session, history) = create_session("spacex", "gpt3")

    question = "Who is the CEO of SpaceX?"
    session.append_user_question(session.manifest.format_question(question))
    process_llm(session)
    messages = history.messages()
    last_message = messages[len(messages) - 1]

    print(f"Q: {question}")
    print(f"A: {last_message.get('content')}")


main()
