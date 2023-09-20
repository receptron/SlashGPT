from typing import List

import os
import requests

from slashgpt.llms.engine.base import LLMEngineBase
from slashgpt.manifest import Manifest
from slashgpt.utils.print import print_debug


def message_to_prompt(messages: List[dict], manifest: Manifest):
    functions = manifest.functions()
    prompts = []
    for message in messages:
        role = message["role"]
        content = message["content"]
        if content:
            prompts.append(f"{role}:{content}")
    if functions:
        # insert before last
        last = prompts.pop()
        prompts.append(
            f"system: Here is the definition of functions available to you to call.\n{functions}\nYou need to generate a json file with 'name' for function name and 'arguments' for argument."
        )
        prompts.append(last)

    prompts.append("assistant:")
    return "\n".join(prompts)


class LLMEngineLocal(LLMEngineBase):
    def __init__(self, llm_model):
        self.llm_model = llm_model
        print("***llm_model", self.llm_model.llm_model_data)
        # LATER: Move them to config file
        self.api_key = os.getenv(self.llm_model.llm_model_data.get("x_api_key"), "")
        self.url = self.llm_model.llm_model_data.get("url")
        # "https://llama2-7b-chat.staging.kubeflow.platform.nedra.app/v2/models/llama2-7b-chat/infer"
        # self.url = "https://bge-base-en.staging.kubeflow.platform.nedra.app/v2/models/bge-base-en/infer"
        return

    def chat_completion(self, messages: List[dict], manifest: Manifest, verbose: bool):
        # temperature = manifest.temperature()
        prompt = message_to_prompt(messages, manifest)

        if verbose:
            print_debug("calling *** local")

        print("calling *** local", self.url)
        arguments = {
            'inputs': [{
                "name": "input-0",
                "data": [prompt],
                "datatype": "BYTES",
                "shape": [-1]
            }]
        }
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': self.api_key
        }
        response = requests.post(self.url, headers=headers, json=arguments)
        print("***response.status_code", response.status_code)
        print("***response.text", response.text)

        output = ["Hello World"]
        '''
        output = replicate.run(
            replicate_model,
            input={"prompt": prompt},
            temperature=temperature,
        )
        '''
        res = "".join(output)
        function_call = self._extract_function_call(messages[-1], manifest, res)

        role = "assistant"
        if function_call:
            return (role, None, function_call)
        else:
            return (role, res, None)
