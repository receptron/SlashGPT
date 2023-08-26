import pytest

from lib.history.base import ChatHistory
from lib.history.storage.memory import ChatHistoryMemoryStorage


@pytest.fixture
def history():
    memory_history = ChatHistoryMemoryStorage("123")
    history = ChatHistory(memory_history)
    history.append({"name": "1", "data": "1"})
    history.append({"name": "2", "data": "2"})
    history.append({"name": "3", "data": "3"})
    history.append({"name": "4", "data": "4"})
    history.append({"name": "5", "data": "5"})
    return history


def test_get1(history):
    assert history.get(0).get("name") == "1"


def test_get_data1(history):
    assert history.get_data(0, "name") == "1"


def test_set(history):
    data = {"name": "set", "data": "set_data"}
    history.set(2, data)
    assert history.get(2) == data


def test_len(history):
    assert history.len() == 5


def test_last(history):
    assert history.last() == {"name": "5", "data": "5"}


def test_messages(history):
    assert history.messages() == [
        {"name": "1", "data": "1"},
        {"name": "2", "data": "2"},
        {"name": "3", "data": "3"},
        {"name": "4", "data": "4"},
        {"name": "5", "data": "5"},
    ]
