from typing import List

import replicate

from slashgpt.llms.engine.base import LLMEngineBase
from slashgpt.manifest import Manifest


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


class LLMEngineReplicate(LLMEngineBase):
    def __init__(self, llm_model):
        self.llm_model = llm_model
        return

    def chat_completion(self, messages: List[dict], manifest: Manifest, verbose: bool):
        temperature = manifest.temperature()
        replicate_model = self.llm_model.replicate_model()
        prompt = message_to_prompt(messages, manifest)

        output = replicate.run(
            replicate_model,
            input={"prompt": prompt},
            temperature=temperature,
        )
        res = "".join(output)
        function_call = self._extract_function_call(messages[-1], manifest, res)

        role = "assistant"
        if function_call:
            return (role, None, function_call)
        else:
            return (role, res, None)
