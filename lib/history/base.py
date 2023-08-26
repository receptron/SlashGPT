class ChatHistory:
    def __init__(self, repository):
        self.repository = repository

    def append(self, data):
        self.repository.append(data)

    def get(self, index):
        return self.repository.get(index)

    def get_data(self, index, name):
        return self.repository.get_data(index, name)

    def set(self, index, data):
        self.repository.set(index, data)

    def len(self):
        return self.repository.len()

    def last(self):
        return self.repository.last()

    def messages(self):
        return self.repository.messages()

    def append_message(self, role: str, message: str, name=None):
        if name:
            self.append({"role": role, "content": message, "name": name})
        else:
            self.append({"role": role, "content": message})

    def restore(self, data):
        return self.repository.restore(data)

    def md(self, names={}):
        def to_md(data):
            name = names.get(data["role"]) or data["role"]
            if name == "---":
                return ""
            return ("\n").join(["## " + name, "", data["content"].replace("\n", ""), ""])

        return ("\n").join(list(map(to_md, self.messages())))
