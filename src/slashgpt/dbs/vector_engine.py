from abc import ABCMeta, abstractmethod
from typing import List


class VectorEngine(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, verbose: bool):
        pass

    @abstractmethod
    def query_to_vector(self, query: str) -> List[float]:
        pass

    @abstractmethod
    def results_to_articles(self, results: List[str], query: str, messages: List[dict], model_name: str, token_budget: int) -> str:
        pass
