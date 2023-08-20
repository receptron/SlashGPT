from termcolor import colored
import json

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
    
    def arguments(self):
        function_name = self.__get("name")
        arguments = self.__get("arguments") 
        if arguments and isinstance(arguments, str):
            try:
                return json.loads(arguments)      
            except Exception as e:
                print(colored(f"Function {function_name}: Failed to load arguments as json","yellow"))
        return arguments
    

