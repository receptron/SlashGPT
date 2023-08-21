from lib.llms.engine.openai_gpt import LLMEngineOpenAIGPT

class LLMEngineFactory:
    __cache__ = {}
    @classmethod
    def factory(cls, engine_name):
        if engine_name == "openai-gpt":
            return LLMEngineOpenAIGPT()
        if engine_name == "replicate":
            return
        if engine_name == "palm":
            return
        
