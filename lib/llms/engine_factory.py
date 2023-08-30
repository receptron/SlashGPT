from lib.llms.engine.gpt2 import LLMEngineGPT2
from lib.llms.engine.openai_gpt import LLMEngineOpenAIGPT
# from lib.llms.engine.palm import LLMEnginePaLM
# from lib.llms.engine.replicate import LLMEngineReplicate
import importlib
import inspect

llm_engine_configs = {
    "openai-gpt": LLMEngineOpenAIGPT,
    "replicate": {
        "module_name": "lib.llms.engine.palm",
        "class_name": "LLMEnginePaLM",
    },
    "palm": {
        "module_name": "lib.llms.engine.replicate",
        "class_name": "LLMEngineReplicate",
    },
}

class LLMEngineFactory:
    __cache__ = {}

    @classmethod
    def factory(cls, engine_name: str, llm_model):
        class_data = llm_engine_configs[engine_name]
        if class_data:
            if inspect.isclass(class_data):
                return class_data(llm_model)
            else:
                module = importlib.import_module(class_data["module_name"])
                my_class = getattr(module, class_data["class_name"])
                return my_class(llm_model)

