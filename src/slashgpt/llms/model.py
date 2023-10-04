import importlib
import inspect
import os
from typing import List

from slashgpt.chat_config import ChatConfig
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


def get_default_llm_model_name(llm_models):
    default_key = next(filter(lambda key: llm_models[key].get("default"), llm_models.keys()), None)
    return llm_models.get(default_key)


def get_default_llm_model(default_llm_models, llm_engine_configs):
    return LlmModel(get_default_llm_model_name(default_llm_models), llm_engine_configs)


def __search_llm_model(llm_model_name: str, llm_models={}):
    llm_model_list = list(map(lambda x: x.get("model_name"), llm_models.values()))
    index = llm_model_list.index(llm_model_name) if llm_model_name in llm_model_list else -1

    if index > -1:
        llm_model = list(llm_models.values())[index]
        return llm_model
    else:
        return get_default_llm_model_name(llm_models)


def get_llm_model_from_manifest(manifest: Manifest, config: ChatConfig):
    model = manifest.model()
    if isinstance(model, dict):
        # This code enables llm model definition embedded in the manifest file
        llm_model = model
        llm_model_name = model.get("model_name")
    else:
        llm_model_name = model
        llm_model = __search_llm_model(llm_model_name, config.llm_models)

    return LlmModel(llm_model, config.llm_engine_configs)


def get_llm_model_from_key(key: str, config: ChatConfig):
    llm_model = config.llm_models.get(key)
    if llm_model:
        return LlmModel(llm_model, config.llm_engine_configs)
    return get_default_llm_model(config.llm_models, config.llm_engine_configs)
