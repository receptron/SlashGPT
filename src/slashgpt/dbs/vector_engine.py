from abc import ABCMeta, abstractmethod
from typing import List

from slashgpt.llms.model import LlmModel


class VectorEngine(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, verbose: bool):
        pass

    @abstractmethod
    def query_to_vector(self, query: str) -> List[float]:
        pass

    @abstractmethod
    def results_to_articles(self, results: List[str], query: str, messages: List[dict], llm_model: LlmModel) -> str:
        pass
