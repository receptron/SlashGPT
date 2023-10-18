from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, List, Optional

import tiktoken  # for counting tokens

from slashgpt.function.function_call import FunctionCall
from slashgpt.utils.print import print_warning

if TYPE_CHECKING:
    from slashgpt.manifest import Manifest


class LLMEngineBase(metaclass=ABCMeta):
    def __init__(self, llm_model):
        self.llm_model = llm_model

    @abstractmethod
    def chat_completion(self, messages: List[dict], manifest: Manifest, verbose: bool):
        pass

    """
    Extract the Python code from the string if the agent is a code interpreter.
    Returns it in the "function call" format.
    """

    def _extract_function_call(self, last_message: dict, manifest: Manifest, res: str, is_openai: bool = False):
        if manifest.get("notebook"):
            lines = res.splitlines()
            codes: Optional[list] = None
            for key in range(len(lines)):
                if self.__is_code(lines, key, is_openai):
                    if codes is None:
                        codes = []
                    else:
                        break
                elif codes is not None:
                    codes.append(lines[key])
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

    def __is_code(self, lines, key, is_openai: bool = False):
        if is_openai:
            if len(lines) == key + 1:  # last line has no next line.
                return lines[key][:3] == "```"
            else:
                if lines[key][:3] == "```":
                    return lines[key + 1].startswith("!pip") or lines[key + 1].startswith("from ") or lines[key + 1].startswith("import ")
            return False
        else:
            return lines[key][:3] == "```"

    def prompt_from_messages(self, messages: List[dict], manifest: Manifest):
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

    """
    is_within_budget method is for vector db/engine.
    """

    def is_within_budget(self, text: str, verbose: bool = False):
        token_budget = self.llm_model.max_token() - 500
        return self.__num_tokens(text) <= token_budget

    def __num_tokens(self, text: str):
        """Calculate the llm token of the text. Because this is for openai, override it if you use another language model."""
        model_name = self.llm_model.name() if self.llm_model.name().startswith("gpt-") else "gpt-3.5-turbo-0613"
        encoding = tiktoken.encoding_for_model(model_name)
        return len(encoding.encode(text))
