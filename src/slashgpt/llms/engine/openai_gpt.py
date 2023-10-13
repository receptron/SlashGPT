import sys
from typing import List

import openai

from slashgpt.function.function_call import FunctionCall
from slashgpt.llms.engine.base import LLMEngineBase
from slashgpt.manifest import Manifest
from slashgpt.utils.print import print_debug, print_error


class LLMEngineOpenAIGPT(LLMEngineBase):
    def __init__(self, llm_model):
        self.llm_model = llm_model
        key = llm_model.get_api_key_value()
        if key == "":
            print_error("OPENAI_API_KEY environment variable is missing from .env")
            sys.exit()
        openai.api_key = key

        # Override default openai endpoint for custom-hosted models
        api_base = llm_model.get_api_base()
        if api_base:
            openai.api_base = api_base

        return

    def chat_completion(self, messages: List[dict], manifest: Manifest, verbose: bool):

        model_name = self.llm_model.name()
        temperature = manifest.temperature()
        functions = manifest.functions()
        stream = manifest.stream()
        logprobs = manifest.logprobs()
        num_completions = manifest.num_completions()

        if functions:
            response = openai.ChatCompletion.create(
                model=model_name,
                messages=messages,
                functions=functions,
                temperature=temperature,
            )
        else:
            response = openai.ChatCompletion.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                stream=stream,
                logprobs=logprobs,
                n=num_completions
            )

        if verbose:
            print_debug(f"model={response['model']}")
            print_debug(f"usage={response['usage']}")
        answer = response["choices"][0]["message"]
        res = answer["content"]
        role = answer["role"]
        function_call = FunctionCall.factory(answer.get("function_call"), manifest)

        if res and function_call is None:
            function_call = self._extract_function_call(messages[-1], manifest, res, True)

        return (role, res, function_call)
