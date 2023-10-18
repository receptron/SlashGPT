import glob
import json
import os
from datetime import datetime
from typing import List

from slashgpt.history.storage.abstract import ChatHistoryAbstractStorage
from slashgpt.history.storage.log import create_log_dir, save_log
from slashgpt.utils.print import print_warning


class ChatHistoryMemoryStorage(ChatHistoryAbstractStorage):
    def __init__(self, uid: str, agent_name: str):
        self.__messages: List[dict] = []
        self.uid = uid
        self.agent_name = agent_name
        self.base_dir = "output"

        self.time = datetime.now()
        # init log dir
        create_log_dir(self.base_dir, agent_name)

    def _data(self):
        return {"messages": self.__messages}

    def append(self, data: dict):
        self.__messages.append(data)
        save_log(self.base_dir, self.agent_name, self._data(), self.time)

    def get(self, index: int):
        return self.__messages[index]

    def get_data(self, index: int, name: str):
        m = self.__messages[index]
        if m:
            return m.get(name)

    def set(self, index: int, data: dict):
        if self.__messages[index]:
            self.__messages[index] = data

    def len(self):
        return len(self.__messages)

    def last(self):
        if self.len() > 0:
            return self.__messages[self.len() - 1]

    def pop(self):
        if self.len() > 0:
            return self.__messages.pop()

    def messages(self):
        return self.__messages

    def preset_messages(self):
        return filter(lambda x: x.get("preset"), self.__messages)

    def nonpreset_messages(self):
        return filter(lambda x: not x.get("preset"), self.__messages)

    def restore(self, data: List[dict]):
        self.__messages = data

    def session_list(self):
        history_path = f"./{self.base_dir}/{self.agent_name}"
        files = glob.glob(f"{history_path}/*")
        return list(map(lambda x: {"name": x[1], "id": x[0]}, enumerate(files)))

    def get_session_data(self, id: str):
        files = self.session_list()
        if id.isdecimal() and len(files) > int(id):
            file_name = files[int(id)]["name"]
            if not os.path.exists(file_name):
                print_warning(f"No log named {file_name}")
                return
            with open(file_name, "r", encoding="utf-8") as f:
                log = json.load(f)
                return log
