from abc import ABCMeta, abstractmethod
from typing import List, Optional

from slashgpt.function.function_call import FunctionCall
from slashgpt.manifest import Manifest
from slashgpt.utils.print import print_warning


class LLMEngineBase(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, llm_model):
        pass

    @abstractmethod
    def chat_completion(self, messages: List[dict], manifest: Manifest, verbose: bool):
        pass

    """
    Extract the Python code from the string if the agent is a code interpreter.
    Returns it in the "function call" format.
    """

    def _extract_function_call(self, last_message: dict, manifest: Manifest, res: str):
        if manifest.get("notebook"):
            lines = res.splitlines()
            codes: Optional[list] = None
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
                        "arguments": {"code": codes, "query": last_message["content"]},
                    },
                    manifest,
                )

            print_warning("Debug Message: no code in this reply")
        return None
