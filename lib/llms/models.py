llms = {
    "gpt3": {
        "engine": "openai-gpt",
        "model_name": "gpt-3.5-turbo-0613",
        "max_token": 4096,
    },
    "gpt31": {
        "engine": "openai-gpt",
        "model_name": "gpt-3.5-turbo-16k-0613",
        "max_token": 4096 * 4
    },
    "gpt4": {
        "engine": "openai-gpt",
        "model_name": "gpt-4-0613",
        "max_token": 4096,
    },
    "llama2": {
        "engine": "replicate",
        "model_name": "llama2",
        "api_key": "REPLICATE_API_TOKEN",
        "replicate_model": "a16z-infra/llama7b-v2-chat:a845a72bb3fa3ae298143d13efa8873a2987dbf3d49c293513cd8abf4b845a83",
    },
    "llama270": {
        "engine": "replicate",
        "model_name": "llama270",
        "api_key": "REPLICATE_API_TOKEN",
        "replicate_model": "replicate/llama70b-v2-chat:2d19859030ff705a87c746f7e96eea03aefb71f166725aee39692f1476566d48",
    },
    "vicuna": {
        "engine": "replicate",
        "model_name": "vicuna",
        "api_key": "REPLICATE_API_TOKEN",
        "replicate_model": "replicate/vicuna-13b:6282abe6a492de4145d7bb601023762212f9ddbbe78278bd6771c8b3b2f2a13b",
    },
    "palm": {
        "engine": "palm",
        "model_name": "palm",
        "api_key": "GOOGLE_PALM_KEY",
    },
}


def search_llm_model(llm_model_name):
    llm_model_list = list(map(lambda x: x.get("model_name"), llms.values()))
    index = llm_model_list.index(llm_model_name) if llm_model_name in llm_model_list else -1

    if index > -1: 
        llm_model = list(llms.values())[index]
        return llm_model
    else:
        return llms.get("gpt3")
