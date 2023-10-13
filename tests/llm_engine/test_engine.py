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
        return (role, res, function_call)


my_llm_engine_configs = {
    "my_engine": MockLlmEngine,
}

my_llm_models = {
    "my_model": {
        "engine_name": "my_engine",
        "model_name": "my_model",
    },
}


class Test:
    def process_event(self, callback_type, data):
        if callback_type == "bot":
            self.res = data  # record the output from the LLM

    def test_simple(self):
        config = ChatConfig(current_dir, my_llm_models, my_llm_engine_configs)
        manifest = {"model": "my_model", "prompt": "This is prompt"}
        session = ChatSession(config, manifest=manifest)
        session.append_user_question("Hi")
        session.call_loop(self.process_event)
        assert self.res == "Hello World"
        session.append_user_question("Bye")
        session.call_loop(self.process_event)
        assert self.res == "Sayonara"
        session.append_user_question("Repeat this message.")
        session.call_loop(self.process_event)
        assert self.res == "Repeat this message."
        session.append_user_question("prompt")
        session.call_loop(self.process_event)
        assert self.res == manifest.get("prompt")

    def test_memory(self):
        config = ChatConfig(current_dir, my_llm_models, my_llm_engine_configs)
        manifest = {"model": "my_model", "prompt": "This is prompt {memory}"}
        memory = {"name": "Joe Smith"}
        session = ChatSession(config, manifest=manifest, memory=memory)
        session.append_user_question("prompt")
        session.call_loop(self.process_event)
        assert self.res == manifest.get("prompt").format(memory=json.dumps(memory))
