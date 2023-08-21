from datetime import datetime
import re
import random
import json

class Manifest:
    def __init__(self, manifest = {}, manifest_name = None):
        self.__manifest = manifest
        self.__manifest_name = manifest_name
        
    def get(self, key):
        return self.__manifest.get(key)

    def username(self):
        return self.get("you") or f"You({self.__manifest_name})"

    def botname(self):
        return self.get("bot") or "GPT"

    def actions(self):
        return self.get("actions") or {}

    def title(self):
        return self.get("title") or ""
    
    def temperature(self):
        if "temperature" in self.__manifest:
            return float(self.get("temperature"))
        return 0.7

    def model(self):
        return self.get("model") or "gpt-3.5-turbo-0613";

    def functions(self):
        value = self.__functions()
        agents = self.get("agents")
        
        if value and agents:
            # WARNING: It assumes that categorize(category, ...) function
            for function in value:
                if function.get("name") == "categorize":
                    function["parameters"]["properties"]["category"]["enum"] = agents
        return value

        
    def __functions(self):
        value = self.get("functions")
        if value:
            if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                return value
            if isinstance(value, str):
                with open(value, 'r') as f:
                    return json.load(f)
        return None
            
    """
    Read Module
    Read Python file if module is in manifest.
    """
    def read_module(self):
        module = self.get("module")
        if module:
            with open(f"{module}", 'r') as f:
                try:
                    code = f.read()
                    namespace = {}
                    exec(code, namespace)
                    print(f" {module}")
                    return namespace
                except ImportError:
                    print(f"Failed to import module: {module}")

        return None

    
    def __read_prompt(self):
        prompt = self.get("prompt")
        if isinstance(prompt, list):
            prompt = '\n'.join(prompt)
        if prompt:
            if re.search("\\{now\\}", prompt):
                time = datetime.now()
                prompt = re.sub("\\{now\\}", time.strftime('%Y%m%dT%H%M%SZ'), prompt, 1)
        return prompt

    """
    Read manifest data and shuffle data
    """
    def __get_random_manifest_data(self):
        data = self.get("data")
        if data:
            # Shuffle 
            for i in range(len(data)):
                j = random.randrange(0, len(data))
                temp = data[i]
                data[i] = data[j]
                data[j] = temp
            return data
        
    def __replace_random(self, prompt, data):
        j = 0
        while(re.search("\\{random\\}", prompt)):
            prompt = re.sub("\\{random\\}", data[j], prompt, 1)
            j += 1
        return prompt

    def __replace_from_resource_file(self, prompt, resource_file_name):
        with open(f"{resource_file_name}", 'r') as f:
            contents = f.read()
            return re.sub("\\{resource\\}", contents, prompt, 1)

    
    def prompt_data(self):
        prompt = self.__read_prompt()
        if prompt:
            data = self.__get_random_manifest_data()
            if data:
                prompt = self.__replace_random(prompt, data)
            resource = self.get("resource")
            if resource:
                prompt = self.__replace_from_resource_file(prompt, resource)
            return prompt
            
