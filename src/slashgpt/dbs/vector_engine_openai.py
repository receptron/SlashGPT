import os
from typing import List

import openai

from slashgpt.dbs.vector_engine import VectorEngine
from slashgpt.llms.model import LlmModel
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

    def results_to_articles(self, results: List[str], query: str, messages: List[dict], llm_model: LlmModel, token_budget: int) -> str:
        articles = ""
        count = 0
        base_token = self.__messages_tokens(messages, llm_model)
        if self.verbose:
            print_debug(f"messages token:{base_token}")
        for article in results:
            article_with_section = f'\n\nSection:\n"""\n{article}\n"""'
            if llm_model.num_tokens(articles + article_with_section + query) + base_token > token_budget:
                break
            else:
                count += 1
                articles += article_with_section
                if self.verbose:
                    print(len(article), llm_model.num_tokens(article))
        if self.verbose:
            print_debug(f"Articles:{count}, Tokens:{llm_model.num_tokens(articles + query)}")
        return articles

    # Returns the total number of tokens in messages
    def __messages_tokens(self, messages: List[dict], llm_model: LlmModel) -> int:
        return sum([llm_model.num_tokens(message["content"]) for message in messages])
