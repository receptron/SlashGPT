import json
import sys
from typing import List

import openai
import tiktoken  # for counting tokens

from slashgpt.llms.engine.base import LLMEngineBase
from slashgpt.manifest import Manifest
from slashgpt.utils.print import print_debug, print_error


class LLMEngineOpenAILegacy(LLMEngineBase):
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
        prompt = self.prompt_from_messages(messages, manifest)
        params = dict(
            model=self.llm_model.name(),
            prompt=prompt,
            temperature=manifest.temperature(),
            stream=manifest.stream(),
            n=manifest.num_completions(),
            logprobs=manifest.logprobs(),
            max_tokens=self.llm_model.max_token() - self.num_tokens(prompt),
        )

        if verbose:
            print_debug(f"params={json.dumps(params, indent=2)}")
        response = openai.Completion.create(**params)

        if verbose:
            print_debug(f"response={response}")

        res = response["choices"][0]["text"]
        function_call = self._extract_function_call(messages[-1], manifest, res)
        role = "assistant"

        return (role, res, function_call)

    def __num_tokens(self, text: str):
        model_name = self.llm_model.name()
        encoding = tiktoken.encoding_for_model(model_name)
        return len(encoding.encode(text))

    def is_within_budget(self, text: str, verbose: bool = False):
        token_budget = self.llm_model.max_token() - 500
        return self.__num_tokens(text) <= token_budget
