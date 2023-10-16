from abc import ABCMeta, abstractmethod
from typing import List

from slashgpt.dbs.vector_engine import VectorEngine
from slashgpt.llms.model import LlmModel


class VectorDBBase(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, embeddings: dict, vector_engine: VectorEngine, verbose: bool):
        self.verbose: bool = verbose
        self.vectorEngine: VectorEngine = vector_engine(verbose)
        self.embeddings: dict = embeddings

    @abstractmethod
    def fetch_data(self, query_embedding: List[float]) -> List[str]:
        pass

    # Fetch artciles related to user messages
    def fetch_related_articles(self, messages: List[dict], llm_model: LlmModel) -> str:
        """Return related articles with the question using the embedding vector search."""
        query = self.messages_to_query(messages)
        query_embedding = self.query_to_vector(query)
        results = self.fetch_data(query_embedding)
        return self.results_to_articles(results, query, messages, llm_model)

    def messages_to_query(self, messages: List[dict]) -> str:
        query = ""
        for message in messages:
            if message["role"] == "user":
                query = message["content"] + "\n" + query
        return query

    def query_to_vector(self, query: str) -> List[float]:
        return self.vectorEngine.query_to_vector(query)

    def results_to_articles(self, results: List[str], query: str, messages: List[dict], llm_model: LlmModel) -> str:
        return self.vectorEngine.results_to_articles(results, query, messages, llm_model)
