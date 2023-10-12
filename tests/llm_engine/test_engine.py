import os
import sys
from typing import List
from dotenv import load_dotenv
import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "../../src"))

from slashgpt.llms.engine.base import LLMEngineBase  # noqa: E402
from slashgpt.manifest import Manifest  # noqa: E402

from slashgpt.chat_config import ChatConfig  # noqa: E402
from slashgpt.chat_session import ChatSession  # noqa: E402

load_dotenv()
current_dir = os.path.dirname(__file__)

class MyLlmEngine(LLMEngineBase):
    def __init__(self, llm_model):
        self.llm_model = llm_model
        return
    
    def chat_completion(self, messages: List[dict], manifest: Manifest, verbose: bool):
        role = "assistant"
        res = "hello"
        function_call = None
        return (role, res, function_call)

my_llm_engine_configs = {
    "my_engine": MyLlmEngine,
}

my_llm_models = {
    "my_model": {
        "engine_name": "my_engine",
        "model_name": "my_model",
    },
}

@pytest.fixture
def engine():
    return MyLlmEngine({})

def test_foo(engine):
    (role, res, function_call) = engine.chat_completion([], None, False)
    assert role == "assistant"
    assert res == "hello"

class Test:
    def process_event(self, callback_type, data):
        if callback_type == "bot":
            self.res = data

    def test_gpt(self, engine):
        config = ChatConfig(current_dir)
        session = ChatSession(config, manifest={})
        session.append_user_question("Which year was the declaration of independence written?")
        session.call_loop(self.process_event)
        assert "1776" in self.res

    def test_gpt(self):
        config = ChatConfig(current_dir, my_llm_models, my_llm_engine_configs)
        session = ChatSession(config, manifest={ "model": "my_model" })
        session.append_user_question("Hi")
        session.call_loop(self.process_event)
        assert self.res == "hello"