from abc import ABCMeta, abstractmethod

from termcolor import colored

from lib.function.function_call import FunctionCall


class LLMEngineBase(metaclass=ABCMeta):
    @abstractmethod
    def chat_completion(self, messages, manifest, llm_model, verbose):
        return

    """
    Extract the Python code from the string if the agent is a code interpreter.
    Returns it in the "function call" format.
    """

    def _extract_function_call(self, messages, manifest, res: str):
        if manifest.get("notebook"):
            lines = res.splitlines()
            codes = None
            for line in lines:
                if line[:3] == "```":
                    if codes is None:
                        codes = []
                    else:
                        break
                elif codes is not None:
                    codes.append(line)
            if codes:
                return FunctionCall(
                    {
                        "name": "run_python_code",
                        "arguments": {"code": codes, "query": messages[-1]["content"]},
                    },
                    manifest,
                )

            print(colored("Debug Message: no code in this reply", "yellow"))
        return None
