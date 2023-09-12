import os
import sys

import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "../../src"))

from slashgpt.history.base import ChatHistory
from slashgpt.history.storage.memory import ChatHistoryMemoryStorage


@pytest.fixture
def history():
    memory_history = ChatHistoryMemoryStorage("123", "key")
    history = ChatHistory(memory_history)
    history.append({"name": "1", "content": "1"})
    history.append({"name": "2", "content": "2"})
    history.append({"name": "3", "content": "3"})
    history.append({"name": "4", "content": "4"})
    history.append({"name": "5", "content": "5"})
    return history


def test_get1(history):
    assert history.get(0).get("name") == "1"


def test_get_data1(history):
    assert history.get_data(0, "name") == "1"


def test_set(history):
    data = {"name": "set", "content": "set_data", "role": None}
    history.set(2, data)
    assert history.get(2) == data


def test_len(history):
    assert history.len() == 5


def test_last(history):
    assert history.last() == {"name": "5", "content": "5", "role": None}


def test_messages(history):
    assert history.messages() == [
        {"name": "1", "content": "1", "role": None},
        {"name": "2", "content": "2", "role": None},
        {"name": "3", "content": "3", "role": None},
        {"name": "4", "content": "4", "role": None},
        {"name": "5", "content": "5", "role": None},
    ]
