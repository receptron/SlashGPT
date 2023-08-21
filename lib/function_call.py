from termcolor import colored
import json

from lib.function_action import FunctionAction

class FunctionCall:
    @classmethod
    def factory(cls, function_call_data):
        if function_call_data == None:
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
        return "name" in self.__function_call_data;
    
    def arguments(self):
        function_name = self.__get("name")
        arguments = self.__get("arguments") 
        if arguments and isinstance(arguments, str):
            try:
                return json.loads(arguments)      
            except Exception as e:
                print(colored(f"Function {function_name}: Failed to load arguments as json","yellow"))
        return arguments
    
    def set_action(self, actions):
        action = actions.get(self.name())
        self.function_action = FunctionAction.factory(action)


    def arguments_for_notebook(self, messages): 
        arguments = self.arguments()
        if self.name() == "python" and isinstance(arguments, str):
            print(colored("python function was called", "yellow"))
            return {
                "code": arguments,
                "query": self.messages[-1]["content"]
            }
        return arguments
            
