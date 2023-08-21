import replicate
from termcolor import colored
from lib.llms.engine.base import LLMEngineBase
from lib.function_call import FunctionCall

class LLMEnginePaLM(LLMEngineBase):
    def __init__(self):
        return

    def chat_completion(self, messages, manifest, llm_model, verbose):
        temperature = manifest.temperature()
        functions = manifest.functions()
        model_name = llm_model.name()
        
        defaults = {
            'model': 'models/chat-bison-001',
            'temperature': temperature,
            'candidate_count': 1,
            'top_k': 40,
            'top_p': 0.95,
        }
        system = ""
        examples = []
        messages = []
        for message in messages:
            role = message["role"]
            content = message["content"]
            if content:
                if role == "system":
                    system = message["content"]
                elif len(messages)>0 or role != "assistant":
                    messages.append(message["content"])

        response = palm.chat(
            **defaults,
            context=system,
            examples=examples,
            messages=messages
        )
        res = response.last
        if res:
            if verbose:
                print(colored(res, "magenta"))
            (function_call, res) = self._extract_function_call(res)
        else:
            # Error: Typically some restrictions
            print(colored(response.filters, "red"))
        return (role, res, function_call)

