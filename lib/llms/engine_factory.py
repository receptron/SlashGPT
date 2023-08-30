from lib.llms.engine.openai_gpt import LLMEngineOpenAIGPT
from lib.llms.engine.palm import LLMEnginePaLM
from lib.llms.engine.replicate import LLMEngineReplicate
from lib.llms.engine.gpt2 import LLMEngineGPT2


class LLMEngineFactory:
    __cache__ = {}

    @classmethod
    def factory(cls, engine_name: str):
        print(engine_name)
        if engine_name == "openai-gpt":
            return LLMEngineOpenAIGPT()
        if engine_name == "replicate":
            return LLMEngineReplicate()
        if engine_name == "palm":
            return LLMEnginePaLM()
        if engine_name == "gpt2":
            return LLMEngineGPT2()
        
