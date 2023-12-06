from __future__ import annotations

import sys
from typing import TYPE_CHECKING, List

import tiktoken  # for counting tokens
from openai import OpenAI

from slashgpt.function.function_call import FunctionCall
from slashgpt.llms.engine.base import LLMEngineBase
from slashgpt.utils.print import print_debug, print_error

if TYPE_CHECKING:
    from slashgpt.llms.model import LlmModel
    from slashgpt.manifest import Manifest


class LLMEngineOpenAIGPT(LLMEngineBase):
    def __init__(self, llm_model: LlmModel):
        super().__init__(llm_model)
        key = llm_model.get_api_key_value()
        if key == "":
            print_error("OPENAI_API_KEY environment variable is missing from .env")
            sys.exit()
        self.client = OpenAI(api_key=key)

        # Override default openai endpoint for custom-hosted models
        api_base = llm_model.get_api_base()
        if api_base:
            self.client.base_url = api_base

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
            if manifest.get("function_call"):
                params["function_call"] = dict(name=manifest.get("function_call"))
        response = self.client.chat.completions.create(**params)
        token_usage = response.usage.total_tokens

        if verbose:
            print_debug(f"model={dict(response)['model']}")
            print_debug(f"usage={dict(response)['usage']}")
        answer = response.choices[0].message
        res = answer.content
        role = answer.role

        function_call = None
        if functions is not None and answer.function_call is not None:
            function_call = FunctionCall(answer.function_call, manifest)

            if res and function_call is None:
                function_call = self._extract_function_call(messages[-1], manifest, res, True)

        return (role, res, function_call, token_usage)

    def __num_tokens(self, text: str):
        model_name = self.llm_model.name()
        encoding = tiktoken.encoding_for_model(model_name)
        return len(encoding.encode(text))

    def is_within_budget(self, text: str, verbose: bool = False):
        token_budget = self.llm_model.max_token() - 500
        return self.__num_tokens(text) <= token_budget
