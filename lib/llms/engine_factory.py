from lib.llms.engine.openai_gpt import LLMEngineOpenAIGPT
from lib.llms.engine.palm import LLMEnginePaLM
from lib.llms.engine.replicate import LLMEngineReplicate


class LLMEngineFactory:
    @classmethod
    def factory(cls, engine_name: str):
        if engine_name == "openai-gpt":
            return LLMEngineOpenAIGPT()
        if engine_name == "replicate":
            return LLMEngineReplicate()
        if engine_name == "palm":
            return LLMEnginePaLM()
