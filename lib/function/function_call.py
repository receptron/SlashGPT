import json

from termcolor import colored

from lib.function.function_action import FunctionAction


class FunctionCall:
    @classmethod
    def factory(cls, function_call_data):
        if function_call_data is None:
            return None
        return FunctionCall(function_call_data)

    def __init__(self, function_call_data):
        self.__function_call_data = function_call_data

    def __get(self, key):
        return self.__function_call_data.get(key)

    def data(self):
        return self.__function_call_data

    def __name(self):
        return self.__get("name")

    def __arguments(self):
        function_name = self.__get("name")
        arguments = self.__get("arguments")
        if arguments and isinstance(arguments, str):
            try:
                return json.loads(arguments)
            except Exception:
                print(
                    colored(
                        f"Function {function_name}: Failed to load arguments as json",
                        "yellow",
                    )
                )
        return arguments

    def set_action(self, actions):
        action = actions.get(self.__name())
        self.function_action = FunctionAction.factory(action)

    def emit_data(self):
        if self.function_action and self.function_action.has_emit():
            return (
                self.function_action.emit_data(self.__arguments()),
                self.function_action.emit_method(),
            )
        return (None, None)

    def __arguments_for_notebook(self, messages):
        arguments = self.__arguments()
        if self.__name() == "python" and isinstance(arguments, str):
            print(colored("python function was called", "yellow"))
            return {"code": arguments, "query": messages[-1]["content"]}
        return arguments

    def process_function_call(self, manifest, history, runtime, verbose=False):
        function_name = self.__name()
        if function_name is None:
            return (None, None, False)

        function_message = None
        arguments = self.__arguments()

        print(colored(json.dumps(self.data(), indent=2), "blue"))

        if self.function_action:
            # call external api or some
            function_message = self.function_action.call_api(arguments, verbose)
        else:
            if manifest.get("notebook"):
                # Python code from llm
                arguments = self.__arguments_for_notebook(history.messages())
                function = getattr(runtime, function_name)
            else:
                # Python code from resource file
                function = manifest.get_module(function_name)  # python code
            if function:
                if isinstance(arguments, str):
                    (result, message) = function(arguments)
                else:
                    (result, message) = function(**arguments)

                if message:
                    # Embed code for the context
                    history.append_message("assistant", message)
                function_message = self.__format_python_result(manifest, result)
            else:
                print(colored(f"No function {function_name} in the module", "red"))

        if function_message:
            history.append_message("function", function_message, function_name)

        should_call_llm = (not manifest.skip_function_result()) and function_message
        return (function_message, function_name, should_call_llm)

    def __format_python_result(self, manifest, result):
        if isinstance(result, dict):
            result = json.dumps(result)
        result_form = manifest.get("result_form")
        if result_form:
            return result_form.format(result=result)
        return result
