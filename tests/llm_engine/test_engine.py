import json
import os
import sys
from typing import List

from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "../../src"))

from slashgpt.chat_config import ChatConfig  # noqa: E402
from slashgpt.chat_session import ChatSession  # noqa: E402
from slashgpt.llms.engine.base import LLMEngineBase  # noqa: E402
from slashgpt.manifest import Manifest  # noqa: E402

load_dotenv()
current_dir = os.path.dirname(__file__)


class MockLlmEngine(LLMEngineBase):
    def __init__(self, llm_model):
        super().__init__(llm_model)

    def chat_completion(self, messages: List[dict], manifest: Manifest, verbose: bool):
        role = "assistant"
        function_call = None
        res = "no message"
        if len(messages) > 0:
            last_message = messages[len(messages) - 1].get("content")
            res = last_message or ""  # just repeat if there is no mathing message
            if last_message == "Hi":
                res = "Hello World"
            elif last_message == "Bye":
                res = "Sayonara"
            elif last_message == "prompt":
                res = messages[0].get("content") or ""
            elif last_message == "model":
                res = self.llm_model.name()
            elif last_message == "custom":
                res = self.llm_model.get("x_custom")
        return (role, res, function_call, 0)


my_llm_engine_configs = {
    "mock_engine": MockLlmEngine,
}
config = ChatConfig(current_dir, llm_engine_configs=my_llm_engine_configs)

mock_model = {
    "engine_name": "mock_engine",
    "model_name": "mock_model",
    "x_custom": "mock_value",
}


class Test:
    def test_simple(self):
        manifest = {
            "model": mock_model,
            "prompt": "This is prompt",
        }
        session = ChatSession(config, manifest=manifest)
        session.append_user_question("Hi")
        (message, _function_call, _) = session.call_llm()
        assert message == "Hello World"
        session.append_user_question("Bye")
        (message, _function_call, _) = session.call_llm()
        assert message == "Sayonara"
        session.append_user_question("Repeat this message.")
        (message, _function_call, _) = session.call_llm()
        assert message == "Repeat this message."
        session.append_user_question("prompt")
        (message, _function_call, _) = session.call_llm()
        assert message == manifest.get("prompt")
        session.append_user_question("model")
        (message, _function_call, _) = session.call_llm()
        assert message == "mock_model"
        session.append_user_question("custom")
        (message, _function_call, _) = session.call_llm()
        assert message == "mock_value"

    def test_memory(self):
        manifest = {
            "model": mock_model,
            "prompt": "This is prompt {memory}",
        }
        memory = {"name": "Joe Smith"}
        session = ChatSession(config, manifest=manifest, memory=memory)
        session.append_user_question("prompt")
        (message, _function_call, _) = session.call_llm()
        assert message == manifest.get("prompt").format(memory=json.dumps(memory))
