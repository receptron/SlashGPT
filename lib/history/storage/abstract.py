from abc import ABCMeta, abstractmethod


class ChatHisoryAbstractStorage(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, uid: str, agent_name: str):
        pass

    @abstractmethod
    def append(self, data):
        pass

    @abstractmethod
    def get(self, index):
        pass

    @abstractmethod
    def get_data(self, index, name):
        pass

    @abstractmethod
    def set(self, index, data):
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
    def restore(self, data):
        pass

    @abstractmethod
    def session_list(self):
        pass

    @abstractmethod
    def get_session_data(self, id: str):
        pass
