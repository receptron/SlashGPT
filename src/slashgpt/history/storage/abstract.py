from abc import ABCMeta, abstractmethod
from typing import List


class ChatHistoryAbstractStorage(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, uid: str, agent_name: str):
        pass

    @abstractmethod
    def append(self, data: dict):
        pass

    @abstractmethod
    def get(self, index: int):
        pass

    @abstractmethod
    def get_data(self, index: int, name: str):
        pass

    @abstractmethod
    def set(self, index: int, data: dict):
        pass

    @abstractmethod
    def len(self):
        pass

    @abstractmethod
    def last(self):
        pass

    @abstractmethod
    def pop(self):
        pass

    @abstractmethod
    def messages(self):
        pass

    @abstractmethod
    def restore(self, data: List[dict]):
        pass

    @abstractmethod
    def session_list(self):
        pass

    @abstractmethod
    def get_session_data(self, id: str):
        pass
