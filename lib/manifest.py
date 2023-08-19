from datetime import datetime
import re
import random
import json

class Manifest:
    def __init__(cls, manifest = {}, manifest_key = None):
        cls.__manifest = manifest
        cls.__manifest_key = manifest_key
        
    def get(cls, key):
        return cls.__manifest.get(key)

    def username(cls):
        return cls.get("you") or f"You({cls.__manifest_key})"

    def botname(cls):
        return cls.get("bot") or "GPT"

    def actions(cls):
        return cls.get("actions") or {}

    def title(cls):
        return cls.get("title") or ""
    
    def temperature(cls):
        if "temperature" in cls.__manifest:
            return float(cls.get("temperature"))
        return 0.7

    def model(cls):
        return cls.get("model") or "gpt-3.5-turbo-0613";

    def function(cls):
        functions_file = cls.get("functions")
        if functions_file:
            with open(functions_file, 'r') as f:
                return json.load(f)
        return None
            
    """
    Read Module
    Read Python file if module is in manifest.
    """
    def read_module(cls):
        module = cls.get("module")
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

    
    def __read_prompt(cls):
        prompt = cls.get("prompt")
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
    def __get_random_manifest_data(cls):
        data = cls.get("data")
        if data:
            # Shuffle 
            for i in range(len(data)):
                j = random.randrange(0, len(data))
                temp = data[i]
                data[i] = data[j]
                data[j] = temp
            return data
        
    def __replace_random(cls, prompt, data):
        j = 0
        while(re.search("\\{random\\}", prompt)):
            prompt = re.sub("\\{random\\}", data[j], prompt, 1)
            j += 1
        return prompt

    def __replace_from_resource_file(cls, prompt, resource_file_name):
        with open(f"{resource_file_name}", 'r') as f:
            contents = f.read()
            return re.sub("\\{resource\\}", contents, prompt, 1)

    
    def prompt_data(cls):
        prompt = cls.__read_prompt()
        if prompt:
            data = cls.__get_random_manifest_data()
            if data:
                prompt = cls.__replace_random(prompt, data)
            resource = cls.get("resource")
            if resource:
                prompt = cls.__replace_from_resource_file(prompt, resource)
            return prompt
            
