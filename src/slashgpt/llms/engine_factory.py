import importlib
import inspect

from slashgpt.utils.print import print_error


class LLMEngineFactory:
    llm_engine_configs: dict = {}

    @classmethod
    def factory(cls, engine_name: str, llm_model):
        class_data = cls.llm_engine_configs.get(engine_name)
        if class_data:
            if inspect.isclass(class_data):
                return class_data(llm_model)
            else:
                module = importlib.import_module(class_data["module_name"])
                my_class = getattr(module, class_data["class_name"])
                return my_class(llm_model)
        else:
            print_error("No engine name: " + engine_name)
