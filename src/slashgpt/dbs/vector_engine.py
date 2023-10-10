from abc import ABCMeta, abstractmethod


class VectorEngine(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, verbose):
        pass

    def query_to_vector(self, query):
        pass

    def results_to_articles(self, results, query, messages, model_name: str, token_budget: int):
        pass
