from typing import List


class ChatContext:
    def __init__(self, repository):
        self.repository = repository

    def setMemory(self, memory: dict, merge: bool = True):
        if merge:
            merged_memory = self.memory().copy()
            merged_memory.update(memory)
            memory = merged_memory
        self.repository.setMemory(memory)

    def memory(self):
        return self.repository.memory()

    def append_message(self, data: dict):
        self.repository.append(data)

    def get_message(self, index: int):
        return self.message_dict(self.repository.get(index))

    def get_message_prop(self, index: int, name: str):
        return self.repository.get_data(index, name)

    def set_message(self, index: int, data: dict):
        self.repository.set(index, data)

    def len_messages(self):
        return self.repository.len()

    def last_message(self):
        return self.message_dict(self.repository.last())

    def pop_message(self):
        return self.repository.pop()

    def message_dict(self, x):
        if x.get("name"):
            return {"role": x.get("role"), "content": x.get("content"), "name": x.get("name")}
        return {"role": x.get("role"), "content": x.get("content")}

    def messages(self):
        return list(map(self.message_dict, self.repository.messages()))

    def preset_messages(self):
        return list(map(self.message_dict, self.repository.preset_messages()))

    def nonpreset_messages(self):
        return list(map(self.message_dict, self.repository.nonpreset_messages()))

    def restore(self, data: List[dict]):
        return self.repository.restore(data)

    def session_list(self):
        return self.repository.session_list()

    def get_session_data(self, id):
        return self.repository.get_session_data(id)

    def md(self, names: dict = {}):
        def to_md(data):
            name = names.get(data["role"]) or data["role"]
            if name == "---":
                return ""
            return ("\n").join(["## " + name, "", data["content"].replace("\n", ""), ""])

        return ("\n").join(list(map(to_md, self.messages())))
