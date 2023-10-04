from slashgpt.chat_config import ChatConfig
from slashgpt.llms.model import LlmModel
from slashgpt.manifest import Manifest


def __get_default_llm_model_name(llm_models: dict):
    default_key = next(filter(lambda key: llm_models[key].get("default"), llm_models.keys()), None)
    return llm_models.get(default_key)


def __search_llm_model(llm_model_name: str, llm_models: dict = {}):
    llm_model_list = list(map(lambda x: x.get("model_name"), llm_models.values()))
    index = llm_model_list.index(llm_model_name) if llm_model_name in llm_model_list else -1

    if index > -1:
        llm_model = list(llm_models.values())[index]
        return llm_model
    else:
        return __get_default_llm_model_name(llm_models)


def get_default_llm_model(default_llm_models: dict, llm_engine_configs: dict):
    return LlmModel(__get_default_llm_model_name(default_llm_models), llm_engine_configs)


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
