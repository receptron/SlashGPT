class FunctionAction:
    @classmethod
    def factory(cls, function_action_data):
        if function_action_data == None:
            return None
        return FunctionAction(function_action_data)


    def __init__(self, function_action_data):
        self.__function_action_data = function_action_data

    def __get(self, key):
        return self.__function_action_data.get(key)        

    def get(self, key):
        return self.__function_action_data.get(key)        

    
    def is_switch_context(self):
        return "metafile" in self.__function_action_data

    def get_manifest_key(self, arguments):
        metafile = self.__get("metafile")
        return metafile.format(**arguments)


