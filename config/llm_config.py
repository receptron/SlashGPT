from slashgpt.llms.engine.openai_gpt import LLMEngineOpenAIGPT

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
}
