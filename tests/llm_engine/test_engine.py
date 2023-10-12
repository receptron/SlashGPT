import os
import sys
from typing import List

import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "../../src"))

from slashgpt.llms.engine.base import LLMEngineBase  # noqa: E402
from slashgpt.manifest import Manifest

class TestEngine(LLMEngineBase):
    def __init__(self, llm_model):
        self.llm_model = llm_model
        return
    
    def chat_completion(self, messages: List[dict], manifest: Manifest, verbose: bool):
        role = "assistant"
        res = "hello"
        function_call = None
        return (role, res, function_call)

def test_foo():
    engine = TestEngine({})
    (role, res, function_call) = engine.chat_completion([], None, False)
    assert role == "assistant"