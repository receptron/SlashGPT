import json
from typing import Union

from slashgpt.function.function_action import FunctionAction
from slashgpt.function.jupyter_runtime import PythonRuntime
from slashgpt.history.base import ChatHistory
from slashgpt.manifest import Manifest
from slashgpt.utils.print import print_error, print_warning


class FunctionCall:
    @classmethod
    def factory(cls, function_call_data: dict, manifest: Manifest):
        if function_call_data is None:
            return None
        return FunctionCall(function_call_data, manifest)

    def __init__(self, function_call_data, manifest):
        self.__function_call_data = function_call_data
        self.__manifest = manifest
        actions = self.__manifest.actions()
        self.function_action = FunctionAction.factory(actions.get(self.__name()))

    def __str__(self):
        return f"{self.__name()}: ({self.__arguments(False)})"

    def __get(self, key: str):
        return self.__function_call_data.get(key)

    def data(self):
        return self.__function_call_data

    def __name(self):
        return self.__get("name")

    def emit_data(self, verbose: bool = False):
        if self.function_action and self.function_action.has_emit():
            return (
                self.function_action.emit_data(self.__arguments(verbose)),
                self.function_action.emit_method(),
            )
        return (None, None)

    def __arguments(self, verbose: bool):
        function_name = self.__get("name")
        arguments = self.__get("arguments")
        if arguments and isinstance(arguments, str):
            try:
                return json.loads(arguments)
            except Exception:
                if verbose:
                    print_warning(f"Function {function_name}: Failed to load arguments as json")
        return arguments

    def __function_arguments(self, last_messages: dict, verbose: bool):
        arguments = self.__arguments(verbose)
        if self.__manifest.get("notebook") and self.__name() == "python" and isinstance(arguments, str):
            print_warning("python function was called")
            return {"code": arguments, "query": last_messages["content"]}
        return arguments

    def get_function(self, runtime: PythonRuntime, function_name: str):
        if self.__manifest.get("notebook") and runtime is not None:
            return getattr(runtime, function_name)
        elif self.__manifest.get("module"):
            return self.__manifest.get_module(function_name)  # python code

    def process_function_call(self, history: ChatHistory, runtime: PythonRuntime = None, verbose: bool = False):
        function_name = self.__name()
        if function_name is None:
            return (None, None, False)

        arguments = self.__function_arguments(history.last_message(), verbose)

        if self.function_action:
            function_message = self.function_action.call_api(arguments, self.__manifest.base_dir, verbose)
        else:
            function = self.get_function(runtime, function_name)
            if function:
                if arguments.get("code"):
                    if isinstance(arguments["code"], list):
                        print("\n".join(arguments["code"]))
                    else:
                        print(arguments["code"])
                if isinstance(arguments, str):
                    (result, message) = function(arguments)
                else:
                    (result, message) = function(**arguments)

                if message:
                    # Embed code for the context
                    history.append_message({"role": "assistant", "content": message})
                function_message = self.__format_python_result(result)
            else:
                function_message = None
                print_error(f"No execution for function {function_name}")

        if function_message:
            history.append_message({"role": "function", "content": function_message, "name": function_name})

        should_call_llm = (not self.__manifest.skip_function_result()) and function_message
        return (function_message, function_name, should_call_llm)

    def __format_python_result(self, result: Union[dict, str]):
        if isinstance(result, dict):
            result = json.dumps(result)
        result_form = self.__manifest.get("result_form")
        if result_form:
            return result_form.format(result=result)
        return result
