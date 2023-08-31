from typing import Dict

from lib.llms.llm_model import LlmModel
from lib.manifest import Manifest

llm_models: Dict[str, dict] = {
    "gpt3": {
        "engine_name": "openai-gpt",
        "model_name": "gpt-3.5-turbo-0613",
        "max_token": 4096,
    },
    "gpt31": {
        "engine_name": "openai-gpt",
        "model_name": "gpt-3.5-turbo-16k-0613",
        "max_token": 4096 * 4,
    },
    "gpt4": {
        "engine_name": "openai-gpt",
        "model_name": "gpt-4-0613",
        "max_token": 4096,
    },
    "llama2": {
        "engine_name": "replicate",
        "model_name": "llama2",
        "api_key": "REPLICATE_API_TOKEN",
        "replicate_model": "a16z-infra/llama7b-v2-chat:a845a72bb3fa3ae298143d13efa8873a2987dbf3d49c293513cd8abf4b845a83",
    },
    "llama270": {
        "engine_name": "replicate",
        "model_name": "llama270",
        "api_key": "REPLICATE_API_TOKEN",
        "replicate_model": "replicate/llama70b-v2-chat:2d19859030ff705a87c746f7e96eea03aefb71f166725aee39692f1476566d48",
    },
    "vicuna": {
        "engine_name": "replicate",
        "model_name": "vicuna",
        "api_key": "REPLICATE_API_TOKEN",
        "replicate_model": "replicate/vicuna-13b:6282abe6a492de4145d7bb601023762212f9ddbbe78278bd6771c8b3b2f2a13b",
    },
    "palm": {
        "engine_name": "palm",
        "model_name": "palm",
        "api_key": "GOOGLE_PALM_KEY",
    },
}


def search_llm_model(llm_model_name: str):
    llm_model_list = list(map(lambda x: x.get("model_name"), llm_models.values()))
    index = llm_model_list.index(llm_model_name) if llm_model_name in llm_model_list else -1

    if index > -1:
        llm_model = list(llm_models.values())[index]
        return llm_model
    else:
        return llm_models.get("gpt3")


def get_llm_model_from_manifest(manifest: Manifest):
    llm_model_name = manifest.model()
    llm_model = search_llm_model(llm_model_name)

    return LlmModel(llm_model)


def get_llm_model_from_key(key: str):
    llm_model = llm_models.get(key)
    if llm_model:
        return LlmModel(llm_model)
    return LlmModel(llm_models.get("gpt3"))  # type: ignore[arg-type]
