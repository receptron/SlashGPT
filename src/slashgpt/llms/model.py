import importlib
import inspect
import os
from typing import List

from slashgpt.manifest import Manifest
from slashgpt.utils.print import print_error


class LlmModel:
    def __init__(self, llm_model_data: dict, llm_engine_configs: dict):
        self.llm_model_data = llm_model_data
        self.engine = self.__get_engine(llm_engine_configs)

    def get(self, key: str):
        return self.llm_model_data.get(key)

    def name(self):
        return self.get("model_name")

    def max_token(self):
        return self.get("max_token") or 4096

    def engine_name(self):
        return self.get("engine_name")

    def check_api_key(self):
        if self.get("api_key"):
            return os.getenv(self.get("api_key"), None) is not None
        return True

    def get_api_key_value(self):
        return os.getenv(self.get("api_key"), "")

    def replicate_model(self):
        if self.get("replicate_model"):
            return self.get("replicate_model")

        # TODO default replicate model
        return "a16z-infra/llama7b-v2-chat:a845a72bb3fa3ae298143d13efa8873a2987dbf3d49c293513cd8abf4b845a83"

    def __get_engine(self, llm_engine_configs: dict):
        class_data = llm_engine_configs.get(self.engine_name())

        if class_data:
            if inspect.isclass(class_data):
                return class_data(self)
            else:
                module = importlib.import_module(class_data["module_name"])
                my_class = getattr(module, class_data["class_name"])
                return my_class(self)
        else:
            print_error("No engine name: " + self.engine_name())
            return None

    def generate_response(self, messages: List[dict], manifest: Manifest, verbose: bool):
        return self.engine.chat_completion(messages, manifest, verbose)
