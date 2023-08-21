from abc import ABCMeta, abstractmethod

class LLMEngineBase(metaclass=ABCMeta): 
    @abstractmethod
    def openai_chat_completion(self, messages, manifest, llm_model, verbose ):
        return
