import os
from typing import List

import openai
import tiktoken  # for counting tokens

from slashgpt.dbs.vector_engine import VectorEngine
from slashgpt.utils.print import print_debug


class VectorEngineOpenAI(VectorEngine):
    def __init__(self, verbose: bool):
        self.EMBEDDING_MODEL = os.getenv("PINECONE_EMBEDDING_MODEL", "text-embedding-ada-002")
        self.verbose = verbose

    def query_to_vector(self, query: str) -> List[float]:
        query_embedding_response = openai.Embedding.create(
            model=self.EMBEDDING_MODEL,
            input=query,
        )
        return query_embedding_response["data"][0]["embedding"]

    def results_to_articles(self, results: List[str], query: str, messages: List[dict], model_name: str, token_budget: int) -> str:
        articles = ""
        count = 0
        base_token = self.__messages_tokens(messages, model_name)
        if self.verbose:
            print_debug(f"messages token:{base_token}")
        for article in results:
            article_with_section = f'\n\nSection:\n"""\n{article}\n"""'
            if self.__num_tokens(articles + article_with_section + query, model_name) + base_token > token_budget:
                break
            else:
                count += 1
                articles += article_with_section
                if self.verbose:
                    print(len(article), self.__num_tokens(article, model_name))
        if self.verbose:
            print_debug(f"Articles:{count}, Tokens:{self.__num_tokens(articles + query, model_name)}")
        return articles

    # Returns the total number of tokens in messages
    def __messages_tokens(self, messages: List[dict], model_name: str) -> int:
        return sum([self.__num_tokens(message["content"], model_name) for message in messages])

    # Returns the number of tokens in a string
    def __num_tokens(self, text: str, model_name: str) -> int:
        encoding = tiktoken.encoding_for_model(model_name)
        return len(encoding.encode(text))
