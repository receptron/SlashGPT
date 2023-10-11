from abc import ABCMeta, abstractmethod


class VectorEngine(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, verbose: bool):
        pass

    def query_to_vector(self, query: str):
        pass

    def results_to_articles(self, results, query: str, messages: List[dict], model_name: str, token_budget: int):
        pass
