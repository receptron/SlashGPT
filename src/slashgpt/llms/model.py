import os
from typing import List

from slashgpt.llms.engine_factory import LLMEngineFactory
from slashgpt.manifest import Manifest


class LlmModel:
    def __init__(self, llm_model_data: dict):
        self.llm_model_data = llm_model_data
        self.set_engine()

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

    def set_engine(self):
        self.engine = LLMEngineFactory.factory(self.engine_name(), self)

    def generate_response(self, messages: List[dict], manifest: Manifest, verbose: bool):
        return self.engine.chat_completion(messages, manifest, verbose)


def get_default_llm_model_name(llm_models):
    return llm_models.get("gpt31")


def get_default_llm_model(llm_models):
    return LlmModel(get_default_llm_model_name(llm_models))


def __search_llm_model(llm_model_name: str, llm_models={}):
    llm_model_list = list(map(lambda x: x.get("model_name"), llm_models.values()))
    index = llm_model_list.index(llm_model_name) if llm_model_name in llm_model_list else -1

    if index > -1:
        llm_model = list(llm_models.values())[index]
        return llm_model
    else:
        return get_default_llm_model_name(llm_models)


def get_llm_model_from_manifest(manifest: Manifest, llm_models={}):
    model = manifest.model()
    if isinstance(model, dict):
        # This code enables llm model definition embedded in the manifest file
        llm_model = model
        llm_model_name = model.get("model_name")
    else:
        llm_model_name = model
        llm_model = __search_llm_model(llm_model_name, llm_models)

    return LlmModel(llm_model)


def get_llm_model_from_key(key: str, llm_models={}):
    llm_model = llm_models.get(key)
    if llm_model:
        return LlmModel(llm_model)
    return get_default_llm_model(llm_models)
