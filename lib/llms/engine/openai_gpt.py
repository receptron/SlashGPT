import openai
from termcolor import colored

from lib.function_call import FunctionCall
from lib.llms.engine.base import LLMEngineBase


class LLMEngineOpenAIGPT(LLMEngineBase):
    def __init__(self):
        return

    def chat_completion(self, messages, manifest, llm_model, verbose):
        temperature = manifest.temperature()
        functions = manifest.functions()
        model_name = llm_model.name()
        if functions:
            response = openai.ChatCompletion.create(
                model=model_name,
                messages=messages,
                functions=functions,
                temperature=temperature,
            )
        else:
            response = openai.ChatCompletion.create(
                model=model_name, messages=messages, temperature=temperature
            )
        if verbose:
            print(colored(f"model={response['model']}", "yellow"))
            print(colored(f"usage={response['usage']}", "yellow"))
        answer = response["choices"][0]["message"]
        res = answer["content"]
        role = answer["role"]
        function_call = FunctionCall.factory(answer.get("function_call"))
        return (role, res, function_call)
