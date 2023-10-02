import json
import os
import re
import sys

from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))
sys.path.append(os.path.join(os.path.dirname(__file__), "../tne"))

from config.llm_config_tne import llm_engine_configs, llm_models  # noqa: E402
from slashgpt.chat_session import ChatSession  # noqa: E402
from slashgpt.chat_slash_config import ChatSlashConfig  # noqa: E402
from slashgpt.function.jupyter_runtime import PythonRuntime  # noqa: E402
from slashgpt.history.storage.file import ChatHistoryFileStorage  # noqa: E402
from slashgpt.llms.model import get_llm_model_from_key  # noqa: E402
from slashgpt.utils.print import print_error  # noqa: E402

load_dotenv()
current_dir = os.path.dirname(__file__)

config = ChatSlashConfig(current_dir, current_dir + "/manifests/sample", llm_models, llm_engine_configs)
agent_name = "spacex"
llm_name = "gpt3"
manifest = config.manifests[agent_name]
# print(manifest)
model = get_llm_model_from_key(llm_name, config.llm_models)
# print(model)

engine = ChatHistoryFileStorage("sample", agent_name)
session_id = engine.session_id
print(session_id)
# session = ChatSession(config, manifest=manifest, agent_name=agent_name, history_engine=engine)
# session.set_llm_model(llm_name)
# print (session_id, session, engine)

