from lib.utils.print import print_error
from lib.llms.engine.openai_gpt import LLMEngineOpenAIGPT
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
    "from_pretrained": {
        "module_name": "plugins.engine.from_pretrained",
        "class_name": "LLMEngineFromPretrained",
    },
}

class LLMEngineFactory:
    __cache__ = {}

    @classmethod
    def factory(cls, engine_name: str, llm_model):
        class_data = llm_engine_configs.get(engine_name)
        if class_data:
            if inspect.isclass(class_data):
                return class_data(llm_model)
            else:
                module = importlib.import_module(class_data["module_name"])
                my_class = getattr(module, class_data["class_name"])
                return my_class(llm_model)
        else:
            print_error("No engine name: " + engine_name)
