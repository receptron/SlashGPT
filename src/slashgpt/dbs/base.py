from abc import ABCMeta, abstractmethod


class VectorDBBase(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, table_name: str, verbose: bool):
        self.vectorEngine = None
        pass

    @abstractmethod
    def fetch_data(self, query_embedding):
        pass

    # Fetch artciles related to user messages
    def fetch_related_articles(self, messages, model_name: str, token_budget: int) -> str:
        """Return related articles with the question using the embedding vector search."""
        query = self.messages_to_query(messages)
        query_embedding = self.query_to_vector(query)
        results = self.fetch_data(query_embedding)
        return self.results_to_articles(results, query, messages, model_name, token_budget)

    def messages_to_query(self, messages):
        query = ""
        for message in messages:
            if message["role"] == "user":
                query = message["content"] + "\n" + query
        return query

    def query_to_vector(self, query):
        return self.vectorEngine.query_to_vector(query)

    def results_to_articles(self, results, query, messages, model_name: str, token_budget: int):
        return self.vectorEngine.results_to_articles(results, query, messages, model_name, token_budget)
