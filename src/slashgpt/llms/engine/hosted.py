from __future__ import annotations

import json
from typing import TYPE_CHECKING, List

import requests

from slashgpt.llms.engine.base import LLMEngineBase
from slashgpt.utils.print import print_debug, print_error

if TYPE_CHECKING:
    from slashgpt.llms.model import LlmModel
    from slashgpt.manifest import Manifest


class LLMEngineHosted(LLMEngineBase):
    def __init__(self, llm_model: LlmModel):
        super().__init__(llm_model)
        self.api_key = self.llm_model.get_api_key_value()
        self.header_key = self.llm_model.llm_model_data.get("header_api_key")
        self.url = self.llm_model.llm_model_data.get("url")
        return

    def chat_completion(self, messages: List[dict], manifest: Manifest, verbose: bool):
        # temperature = manifest.temperature()
        prompt = self.prompt_from_messages(messages, manifest)

        if verbose:
            print_debug("calling *** local")

        # print("calling *** local", self.url)
        arguments = {"inputs": [{"name": "input-0", "data": [prompt], "datatype": "BYTES", "shape": [-1]}]}
        headers = {"Content-Type": "application/json", self.header_key: self.api_key}
        response = requests.post(self.url, headers=headers, json=arguments)
        if verbose:
            print("***response.status_code", response.status_code)
            print("***response.text", response.text)

        output = []
        if response.status_code < 300:
            # print("*** success")
            json_data = json.loads(response.text)
            # print(json.dumps(json_data, indent=2))
            outputs = json_data.get("outputs")
            if outputs and isinstance(outputs, list):
                # print("*** found outputs")
                output0 = outputs[0]
                datatype = output0.get("datatype")
                data = output0.get("data")
                if datatype == "BYTES":
                    # print("*** found data", data[0])
                    json_data2 = json.loads(data[0])
                    if json_data2:
                        if verbose:
                            print("json_data2:", json.dumps(json_data2, indent=2))
                        output = json_data2.get("message")
                elif datatype == "FP64":
                    print(datatype, data[0])
                    output = [str(data)]
        else:
            print_error(f"Error:{response.status_code}\n{response.text}")

        if isinstance(output, list):
            if isinstance(output[0], list):
                output00 = output[0][0]
                gen = output00.get("generation")
                res = gen.get("content").strip()
                if verbose:
                    print("content", res)
            else:
                res = "\n" + "".join(output)
        function_call = self._extract_function_call(messages[-1], manifest, res)

        role = "assistant"
        if function_call:
            return (role, None, function_call, None)
        else:
            return (role, res, None, None)
