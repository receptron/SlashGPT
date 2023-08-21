import replicate
from termcolor import colored
from lib.llms.engine.base import LLMEngineBase
from lib.function_call import FunctionCall

class LLMEngineReplicate(LLMEngineBase):
    def __init__(self):
        return

    def chat_completion(self, messages, manifest, llm_model, verbose):
        role = "assistant"
        functions = manifest.functions()
        temperature = manifest.temperature()
        prompts = []
        for message in messages:
            role = message["role"]
            content = message["content"]
            if content:
                prompts.append(f"{role}:{message['content']}")
        if functions:
            last = prompts.pop()
            prompts.append(f"system: Here is the definition of functions available to you to call.\n{functions}\nYou need to generate a json file with 'name' for function name and 'arguments' for argument.")
            prompts.append(last)
        prompts.append("assistant:")
            
        replicate_model = llm_model.replicate_model()
                
        output = replicate.run(
            replicate_model,
            input={"prompt": '\n'.join(prompts)},
            temperature = temperature
        )
        res = ''.join(output)
        function_call = self._extract_function_call(messages, manifest, res)
        if function_call:
            return (role, None, function_call)
        else:
            return (role, res, None)
