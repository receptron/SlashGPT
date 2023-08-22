import pytest
import sys

from lib.chat_history import ChatHistory

@pytest.fixture

def history():
    history = ChatHistory()
    history.append({})
    return history

def test_get1(history):
    assert history.get(0) == {}

