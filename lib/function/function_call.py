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

    def name(self):
        return self.__get("name")

    def should_call(self):
        return "name" in self.__function_call_data

    def arguments(self):
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
        action = actions.get(self.name())
        self.function_action = FunctionAction.factory(action)

    def get_emit_data(self):
        return (self.function_action.emit_data(self.arguments()), self.function_action.emit_method())

    def arguments_for_notebook(self, messages):
        arguments = self.arguments()
        if self.name() == "python" and isinstance(arguments, str):
            print(colored("python function was called", "yellow"))
            return {"code": arguments, "query": messages[-1]["content"]}
        return arguments

    def process_function_call(self, manifest, history, runtime, verbose=False):
        function_message = None
        function_name = self.name()
        arguments = self.arguments()

        print(colored(json.dumps(self.data(), indent=2), "blue"))

        if self.function_action:
            # TODO: Check emit process
            if self.function_action.has_emit():
                function_name = (
                    None  # Without name, this message will be treated as user prompt.
                )

            # call external api or some
            function_message = self.function_action.call_api(arguments, verbose)
        else:
            if manifest.get("notebook"):
                # Python code from llm
                arguments = self.arguments_for_notebook(history.messages())
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
                function_message = self.format_python_result(manifest, result)
            else:
                print(colored(f"No function {function_name} in the module", "red"))

        role = None
        if function_message:
            role = (
                "function"
                if function_name or manifest.skip_function_result()
                else "user"
            )
            history.append_message(role, function_message, function_name)

        should_next_call_llm = (
            not manifest.skip_function_result()
        ) and function_message
        return (function_message, function_name, role, should_next_call_llm)

    def format_python_result(self, manifest, result):
        if isinstance(result, dict):
            result = json.dumps(result)
        result_form = manifest.get("result_form")
        if result_form:
            return result_form.format(result=result)
        return result
