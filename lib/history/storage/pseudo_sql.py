import uuid

from lib.history.storage.abstract import ChatHisoryAbstractStorage


class ChatHistoryPseudoSQLStorage(ChatHisoryAbstractStorage):
    def __init__(self, uid: str, manifest_key: str):
        self.__messages = []
        self.uid = uid
        self.manifest_key = manifest_key
        self.__new_session_id()
        # insert into log_manager (uid, session_id, manifest_key, created_at)
        # VALUES self.uid, self.session_id, manifest_key, timestamp.ms)

    def __new_session_id(self):
        self.session_id = str(uuid.uuid4())

    def append(self, data):
        # insert into log (uid, session_id, role, message, created_at)
        # VALUES self.uid, self.session_id, data[role], data['message'], timestamp.ms )
        self.__messages.append(data)

    def get(self, index):
        # select * from log where uid = self.uid and session_id = self.session_id
        # order by create_at ASC limit 1 offset index
        return self.__messages[index]

    def get_data(self, index, name):
        # select * from log where uid = self.uid and session_id = self.session_id
        # order by create_at ASC limit 1 offset index
        m = self.__messages[index]
        if m:
            return m.get(name)

    def set(self, index, data):
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

    def messages(self):
        # select * from log where uid = self.uid and session_id = self.session_id
        return self.__messages

    def restore(self, data):
        self.__new_session_id()
        for d in data:
            self.append(d)
