llm_models = {
    "gpt2": {
        "engine_name": "from_pretrained",
        "model_name": "rinna/japanese-gpt2-xsmall",
        "max_token": 4096,
    },
    "rinna": {
        "engine_name": "from_pretrained-rinna",
        "model_name": "rinna/bilingual-gpt-neox-4b-instruction-sft",
        "max_token": 4096,
    },
    "code_lama": {
        "engine_name": "code_lama",
        "model_name": "codellama/CodeLlama-7b-hf",
        "max_token": 4096,
    },
}

llm_engine_configs = {
    "from_pretrained": {
        "module_name": "plugins.engine.from_pretrained",
        "class_name": "LLMEngineFromPretrained",
    },
    "from_pretrained-rinna": {
        "module_name": "plugins.engine.from_pretrained2",
        "class_name": "LLMEngineFromPretrained2",
    },
    "code_lama": {
        "module_name": "plugins.engine.code_lama",
        "class_name": "LLMEngineCodeLama",
    },
    "hosted": {
        "module_name": "plugins.engine.hosted",
        "class_name": "LLMEngineHosted",
    },
}
