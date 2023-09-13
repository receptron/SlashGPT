from typing import List

import openai

from slashgpt.function.function_call import FunctionCall
from slashgpt.llms.engine.base import LLMEngineBase
from slashgpt.manifest import Manifest
from slashgpt.utils.print import print_debug


class LLMEngineOpenAIGPT(LLMEngineBase):
    def __init__(self, llm_model):
        self.llm_model = llm_model
        return

    def chat_completion(self, messages: List[dict], manifest: Manifest, verbose: bool):
        temperature = manifest.temperature()
        functions = manifest.functions()
        model_name = self.llm_model.name()
        if functions:
            response = openai.ChatCompletion.create(
                model=model_name,
                messages=messages,
                functions=functions,
                temperature=temperature,
            )
        else:
            response = openai.ChatCompletion.create(model=model_name, messages=messages, temperature=temperature)
        if verbose:
            print_debug(f"model={response['model']}")
            print_debug(f"usage={response['usage']}")
        answer = response["choices"][0]["message"]
        res = answer["content"]
        role = answer["role"]
        function_call = FunctionCall.factory(answer.get("function_call"), manifest)
        return (role, res, function_call)
