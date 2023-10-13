import sys
from typing import List

import openai
import tiktoken  # for counting tokens

from slashgpt.function.function_call import FunctionCall
from slashgpt.llms.engine.base import LLMEngineBase
from slashgpt.manifest import Manifest
from slashgpt.utils.print import print_debug, print_error


class LLMEngineOpenAIGPT(LLMEngineBase):
    def __init__(self, llm_model):
        super().__init__(llm_model)
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
        num_completions = manifest.num_completions()
        # LATER: logprobs is invalid with ChatCompletion API
        # logprobs = manifest.logprobs()
        params = dict(model=model_name, messages=messages, temperature=temperature, stream=stream, n=num_completions)
        if functions:
            params["functions"] = functions
        response = openai.ChatCompletion.create(**params)

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

    def num_tokens(self, text: str):
        model_name = self.llm_model.name()
        encoding = tiktoken.encoding_for_model(model_name)
        return len(encoding.encode(text))

    def is_within_budget(self, text: str):
        token_budget = self.llm_model.max_token() - 500
        return self.num_tokens(text) <= token_budget
