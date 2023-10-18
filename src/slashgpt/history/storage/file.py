import glob
import json
import os
import uuid
from typing import List

from slashgpt.history.storage.abstract import ChatHistoryAbstractStorage
from slashgpt.history.storage.log import create_log_dir
from slashgpt.utils.print import print_warning


class ChatHistoryFileStorage(ChatHistoryAbstractStorage):
    def __init__(self, uid: str, agent_name: str, session_id: str = ""):
        self.__messages: List[dict] = []
        self.base_dir = "filememory"

        self.uid = uid
        self.agent_name = agent_name

        # self.time = datetime.now()

        create_log_dir(self.base_dir, agent_name)
        if session_id == "":
            self.session_id = str(uuid.uuid4())
        else:
            self.session_id = session_id
            self.__load_session()

    def _data(self):
        return {"messages": self.__messages}

    def __save_session(self):
        with open(f"{self.base_dir}/{self.agent_name}/{self.session_id}.json", "w") as f:
            json.dump(self._data(), f, ensure_ascii=False, indent=2)

    def __load_session(self):
        try:
            with open(f"{self.base_dir}/{self.agent_name}/{self.session_id}.json", "r") as f:
                data = json.load(f)
                self.__messages = data.get("messages")
        except FileNotFoundError:
            self.__messages = []

    def append(self, data: dict):
        self.__messages.append(data)
        self.__save_session()

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
