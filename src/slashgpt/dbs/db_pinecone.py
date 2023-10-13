import os
from typing import List

import pinecone

from slashgpt.dbs.db_base import VectorDBBase
from slashgpt.dbs.vector_engine import VectorEngine
from slashgpt.utils.print import print_error


class DBPinecone(VectorDBBase):
    @classmethod
    def factory(cls, table_name: str, embeddings: dict, vector_engine: VectorEngine, verbose: bool):
        pinecone_api_key = os.getenv("PINECONE_API_KEY", "")
        pinecone_environment = os.getenv("PINECONE_ENVIRONMENT", "")

        if table_name and pinecone_api_key and pinecone_environment:
            pinecone.init(api_key=pinecone_api_key, environment=pinecone_environment)
            assert table_name in pinecone.list_indexes(), f"No Pinecone table named {table_name}"
            return DBPinecone(table_name, embeddings, vector_engine, verbose)
        else:
            print_error("PINECONE_API_KEY / PINECONE_ENVIRONMENT environment variable is missing from .env")

    def __init__(self, table_name: str, embeddings: dict, vector_engine: VectorEngine, verbose: bool):
        super().__init__(table_name, embeddings, vector_engine, verbose)
        self.index = pinecone.Index(table_name)

    def fetch_data(self, query_embedding: List[float]) -> List[str]:
        response = self.index.query(query_embedding, top_k=12, include_metadata=True)

        results = []
        for match in response["matches"]:
            results.append(match["metadata"]["text"])

        return results
