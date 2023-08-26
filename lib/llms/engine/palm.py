import google.generativeai as palm
from termcolor import colored

from lib.llms.engine.base import LLMEngineBase
from lib.utils.utils import COLOR_ERROR


class LLMEnginePaLM(LLMEngineBase):
    def __init__(self):
        return

    def chat_completion(self, messages, manifest, llm_model, verbose):
        temperature = manifest.temperature()

        defaults = {
            "model": "models/chat-bison-001",
            "temperature": temperature,
            "candidate_count": 1,
            "top_k": 40,
            "top_p": 0.95,
        }
        system = ""
        examples = []
        new_messages = []
        for message in messages:
            role = message["role"]
            content = message["content"]
            if content:
                if role == "system":
                    system = message["content"]
                elif len(new_messages) > 0 or role != "assistant":
                    new_messages.append(message["content"])

        response = palm.chat(**defaults, context=system, examples=examples, messages=new_messages)
        res = response.last
        if res:
            if verbose:
                print(colored(res, "cyan"))
            function_call = self._extract_function_call(messages, manifest, res)
        else:
            # Error: Typically some restrictions
            print(colored(response.filters, COLOR_ERROR))
        if function_call:
            return (role, None, function_call)
        else:
            return (role, res, None)
