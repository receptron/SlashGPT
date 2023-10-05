import importlib
import inspect
import os
from typing import List

from slashgpt.chat_config import ChatConfig
from slashgpt.manifest import Manifest
from slashgpt.utils.print import print_error


class LlmModel:
    """It represents a LLM model such as Llama2 and GPT3.5"""

    def __init__(self, llm_model_data: dict, llm_engine_configs: dict):
        """Although it is possible to create LlmModel object directly,
        it is a lot easier to create it using one of helper class methods below

        Args:

            llm_model_data (dict): parameters to the LLM model (dict)
            llm_engine_configs (dict): dictionary of LLM engines
        """
        self.llm_model_data = llm_model_data
        """
        Parameters to the LLM model (dict):
        
            engine_name (str): name of the engine (e.g, openai-gpt')
            model_name (str): specific model name (e.g, 'gpt-3.5-turbo-0613')
            api_key (str): name of the env. variable which holds a secret key (e.g, 'OPENAI_API_KEY')
            max_token (str): maximum token length (e.g, 4096)
            default (boolean, optional): True if this is the default model
        """
        self.engine = self.__get_engine(llm_engine_configs)
        """A subclass of LLEngineBase, 
        which implements chat_completion method for a particular LLM
        """

    @classmethod
    def __get_default_llm_model_name(cls, llm_models: dict):
        default_key = next(filter(lambda key: llm_models[key].get("default"), llm_models.keys()), None)
        return llm_models.get(default_key)

    @classmethod
    def __search_llm_model(cls, llm_model_name: str, llm_models: dict = {}):
        llm_model_list = list(map(lambda x: x.get("model_name"), llm_models.values()))
        index = llm_model_list.index(llm_model_name) if llm_model_name in llm_model_list else -1

        if index > -1:
            llm_model = list(llm_models.values())[index]
            return llm_model
        else:
            return cls.__get_default_llm_model_name(llm_models)

    @classmethod
    def get_default_llm_model(cls, default_llm_models: dict, llm_engine_configs: dict):
        return LlmModel(cls.__get_default_llm_model_name(default_llm_models), llm_engine_configs)

    @classmethod
    def get_llm_model_from_manifest(cls, manifest: Manifest, config: ChatConfig):
        model = manifest.model()
        if isinstance(model, dict):
            # This code enables llm model definition embedded in the manifest file
            llm_model = model
            llm_model_name = model.get("model_name")
        else:
            llm_model_name = model
            llm_model = cls.__search_llm_model(llm_model_name, config.llm_models)

        return LlmModel(llm_model, config.llm_engine_configs)

    @classmethod
    def get_llm_model_from_key(cls, key: str, config: ChatConfig):
        llm_model = config.llm_models.get(key)
        if llm_model:
            return LlmModel(llm_model, config.llm_engine_configs)
        return cls.get_default_llm_model(config.llm_models, config.llm_engine_configs)

    def get(self, key: str):
        """Returns the specified property of the model data"""
        return self.llm_model_data.get(key)

    def name(self):
        """Returns the model name"""
        return self.get("model_name")

    def max_token(self):
        """Returns the maximum token length"""
        return self.get("max_token") or 4096

    def engine_name(self):
        """Returns the engine name (key to the llm_engine_configs)"""
        return self.get("engine_name")

    def check_api_key(self):
        """Returns if the required api key is specified in the environment"""
        if self.get("api_key"):
            return os.getenv(self.get("api_key"), None) is not None
        return True

    def get_api_key_value(self):
        """Returns the api key specified in the eivironment"""
        return os.getenv(self.get("api_key"), "")

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
        """It calls the engine's chat_completion method

        Args:

            messages (list of dict): chat messages
            manifest (Manifest): it specifies the behavior of the LLM agent
            verbose (bool): True if it's in verbose mode.
        """
        return self.engine.chat_completion(messages, manifest, verbose)
