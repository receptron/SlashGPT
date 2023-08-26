import glob
import json
import os
from datetime import datetime

from lib.history.storage.abstract import ChatHisoryAbstractStorage
from lib.history.storage.log import create_log_dir, save_log
from lib.utils.print import print_warning


class ChatHistoryMemoryStorage(ChatHisoryAbstractStorage):
    def __init__(self, uid: str, manifest_key: str):
        self.__messages = []
        self.uid = uid
        self.manifest_key = manifest_key
        self.base_dir = "output"

        self.time = datetime.now()
        # init log dir
        create_log_dir(self.base_dir, manifest_key)

    def append(self, data):
        self.__messages.append(data)
        save_log(self.base_dir, self.manifest_key, self.messages(), self.time)

    def get(self, index):
        return self.__messages[index]

    def get_data(self, index, name):
        m = self.__messages[index]
        if m:
            return m.get(name)

    def set(self, index, data):
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

    def restore(self, data):
        self.__messages = data

    def session_list(self):
        history_path = f"./{self.base_dir}/{self.manifest_key}"
        files = glob.glob(f"{history_path}/*")
        return list(map(lambda x: {"name": x[1], "id": x[0]}, enumerate(files)))

    def get_session_data(self, id):
        files = self.session_list()
        if id.isdecimal() and len(files) > int(id):
            file_name = files[int(id)]["name"]
            if not os.path.exists(file_name):
                print_warning(f"No log named {file_name}")
                return
            with open(file_name, "r", encoding="utf-8") as f:
                log = json.load(f)
                return log
