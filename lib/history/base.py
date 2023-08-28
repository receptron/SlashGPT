class ChatHistory:
    def __init__(self, repository):
        self.repository = repository

    def append(self, data: dict):
        self.repository.append(data)

    def get(self, index: int):
        return self.repository.get(index)

    def get_data(self, index: int, name: str):
        return self.repository.get_data(index, name)

    def set(self, index: int, data: dict):
        self.repository.set(index, data)

    def len(self):
        return self.repository.len()

    def last(self):
        return self.repository.last()

    def pop(self):
        return self.repository.pop()

    def messages(self):
        return self.repository.messages()

    def append_message(self, role: str, message: str, name=None):
        if name:
            self.append({"role": role, "content": message, "name": name})
        else:
            self.append({"role": role, "content": message})

    def restore(self, data: [dict]):
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
