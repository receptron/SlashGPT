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

    def results_to_articles(self, results: List[str], query: str, messages: List[dict], llm_model: LlmModel) -> str:
        articles = ""
        count = 0
        message = self.__join_messages(messages)
        for article in results:
            article_with_section = f'\n\nSection:\n"""\n{article}\n"""'
            if llm_model.is_within_budget(articles + article_with_section + query + message):
                count += 1
                articles += article_with_section
                if self.verbose:
                    print(len(article), llm_model.num_tokens(article))
            else:
                break
        if self.verbose:
            print_debug(f"Articles:{count}, Tokens:{llm_model.num_tokens(articles + query)}")
        return articles

    def __join_messages(self, messages: List[dict]) -> str:
        return "\n".join(map(lambda x: x["content"], messages))
