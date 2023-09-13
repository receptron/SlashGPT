from typing import List

import google.generativeai as palm

from slashgpt.llms.engine.base import LLMEngineBase
from slashgpt.manifest import Manifest
from slashgpt.utils.print import print_error


def get_prompt_data(messages: List[dict]):
    system = ""
    new_messages: List[dict] = []
    for message in messages:
        role = message["role"]
        content = message["content"]
        if content:
            if role == "system":
                system = message["content"]
            elif len(new_messages) > 0 or role != "assistant":
                new_messages.append(message["content"])
    return (system, new_messages)


class LLMEnginePaLM(LLMEngineBase):
    def __init__(self, llm_model):
        return

    def chat_completion(self, messages: List[dict], manifest: Manifest, verbose: bool):
        temperature = manifest.temperature()

        defaults = {
            "model": "models/chat-bison-001",
            "temperature": temperature,
            "candidate_count": 1,
            "top_k": 40,
            "top_p": 0.95,
        }
        (system, new_messages) = get_prompt_data(messages)

        response = palm.chat(**defaults, context=system, examples=[], messages=new_messages)
        res = response.last
        if res:
            if verbose:
                print_error(res)
            function_call = self._extract_function_call(messages[-1], manifest, res)
        else:
            # Error: Typically some restrictions
            print_error(response.filters)

        role = "assistant"
        if function_call:
            return (role, None, function_call)
        else:
            return (role, res, None)
