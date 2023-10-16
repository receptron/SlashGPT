import uuid
from typing import List

from slashgpt.history.storage.abstract import ChatHistoryAbstractStorage
from slashgpt.utils.print import print_warning


class ChatHistoryPseudoSQLStorage(ChatHistoryAbstractStorage):
    def __init__(self, uid: str, agent_name: str):
        self.__messages: List[dict] = []
        self.uid = uid
        self.agent_name = agent_name
        self.__new_session_id()
        # insert into log_manager (uid, session_id, agent_name, created_at)
        # VALUES self.uid, self.session_id, agent_name, timestamp.ms)

    def __new_session_id(self):
        self.session_id = str(uuid.uuid4())

    def setMemory(self, memory: dict):
        print_warning("setMemory: to be implemented")

    def memory(self):
        print_warning("memory: to be implemented")
        return {}

    def append(self, data: dict):
        # insert into log (uid, session_id, role, message, created_at)
        # VALUES self.uid, self.session_id, data[role], data['message'], timestamp.ms )
        self.__messages.append(data)

    def get(self, index: int):
        # select * from log where uid = self.uid and session_id = self.session_id
        # order by create_at ASC limit 1 offset index
        return self.__messages[index]

    def get_data(self, index: int, name: str):
        # select * from log where uid = self.uid and session_id = self.session_id
        # order by create_at ASC limit 1 offset index
        m = self.__messages[index]
        if m:
            return m.get(name)

    def set(self, index: int, data: dict):
        # old_data = get(index)
        # db_pkey = old_data.id
        # update log set ~~~ where id = db_pkey
        if self.__messages[index]:
            self.__messages[index] = data

    def len(self):
        # select count(*) log where uid = self.uid and session_id = self.session_id
        return len(self.__messages)

    def last(self):
        # select * from log where uid = self.uid and session_id = self.session_id
        # order by create_at DESC limit 1
        if self.len() > 0:
            return self.__messages[self.len() - 1]

    def pop(self):
        # delete from log where uid = self.uid and session_id = self.session_id
        # order by create_at DESC limit 1
        if self.len() > 0:
            return self.__messages.pop()

    def message_dict(self, x: dict):
        if x.get("name"):
            return {"role": x.get("role"), "content": x.get("content"), "name": x.get("name")}
        return {"role": x.get("role"), "content": x.get("content")}

    def messages(self):
        # select * from log where uid = self.uid and session_id = self.session_id
        return list(map(self.message_dict, self.__messages))

    def restore(self, data: List[dict]):
        self.__new_session_id()
        for d in data:
            self.append(d)

    def session_list(self):
        # select * from log_manager where uid = self.uid
        # return [{id, name: timestamp}]
        return []

    def get_session_data(self, id: str):
        # select * from log where uid = self.uid and session_id = id
        return {}
