from lib.llms.engine.gpt2 import LLMEngineGPT2
from lib.llms.engine.openai_gpt import LLMEngineOpenAIGPT
from lib.llms.engine.palm import LLMEnginePaLM
from lib.llms.engine.replicate import LLMEngineReplicate


class LLMEngineFactory:
    __cache__ = {}

    @classmethod
    def factory(cls, engine_name: str, llm_model):
        if engine_name == "openai-gpt":
            return LLMEngineOpenAIGPT()
        if engine_name == "replicate":
            return LLMEngineReplicate()
        if engine_name == "palm":
            return LLMEnginePaLM()
        if engine_name == "gpt2":
            return LLMEngineGPT2(llm_model)
