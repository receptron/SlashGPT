from datetime import datetime
import re
import random

class Manifest:
    def __init__(cls, manifest = {}, manifest_key = None):
        cls.manifest = manifest
        cls.manifest_key = manifest_key
        
    def get(cls, key):
        return cls.manifest.get(key)

    def username(cls):
        return cls.get("you") or f"You({cls.manifest_key})"

    def botname(cls):
        return cls.get("bot") or "GPT"

    def temperature(cls):
        if "temperature" in cls.manifest:
            return float(cls.manifest.get("temperature"))
        return 0.7

    def read_prompt(cls):
        prompt = cls.manifest.get("prompt")
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
    def get_random_manifest_data(cls):
        data = cls.manifest.get("data")
        if data:
            # Shuffle 
            for i in range(len(data)):
                j = random.randrange(0, len(data))
                temp = data[i]
                data[i] = data[j]
                data[j] = temp
            return data

    """
    Read Module
    Read Python file if module is in manifest.
    """
    def read_module(cls):
        module = cls.manifest.get("module")
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
