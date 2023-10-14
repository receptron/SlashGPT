import os
import sys
from typing import List

import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "../../src"))

from slashgpt.dbs.db_base import VectorDBBase  # noqa: E402
from slashgpt.dbs.vector_engine import VectorEngine  # noqa: E402
from slashgpt.llms.model import LlmModel  # noqa: E402


class VectorEngineMock(VectorEngine):
    def __init__(self, verbose: bool):
        self.verbose = verbose

    # 1
    def query_to_vector(self, query: str) -> List[float]:
        if query.split("\n")[0] == "apple content 2":
            return [1.0, 0.5]
        if query.split("\n")[0] == "banana content 3":
            return [0.1, 0.5]
        return [0.0, 0.0]

    # 3
    def results_to_articles(self, results: List[str], query: str, messages: List[dict], llm_model: LlmModel) -> str:
        return ", ".join(results)


class DBTestVector(VectorDBBase):
    def __init__(self, table_name: str, storage_id: str, vector_engine: VectorEngine, verbose: bool):
        super().__init__(table_name, storage_id, vector_engine, verbose)

    # 2
    def fetch_data(self, query_embedding: List[float]) -> List[str]:
        if query_embedding[0] == 1.0:
            return ["alice", "bob"]
        if query_embedding[0] == 0.1:
            return ["banana", "pineapple"]
        return ["aaa"]


@pytest.fixture
def vector_db():
    return DBTestVector("test", "test", VectorEngineMock, True)


def test_vector1(vector_db):
    messages = [
        {
            "role": "user",
            "content": "apple content 1",
        },
        {
            "role": "user",
            "content": "apple content 2",
        },
    ]
    articles = vector_db.fetch_related_articles(messages, "")
    assert articles == "alice, bob"


def test_vector2(vector_db):
    messages = [
        {
            "role": "content",
            "content": "apple content 1",
        },
        {
            "role": "info",
            "content": "apple content 2",
        },
        {
            "role": "user",
            "content": "banana content 3",
        },
    ]
    articles = vector_db.fetch_related_articles(messages, "")
    assert articles == "banana, pineapple"
