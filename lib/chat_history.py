class ChatHistory:
    def __init__(self):
        self.messages = []

    def append(self, data):
        self.messages.append(data)


    def get(self, index):
        return self.messages[index]

    def get_data(self, index, name):
        m = self.messages[index]
        if m:
            return m.get(name)

    def set(self, index, data):
        if self.messages[index]:
            self.messages[index] = data

    def len(self):
        return len(self.messages)

    def last(self):
        if self.len() > 0:
            return self.messages[self.len() - 1]

    def all_data(self):
        return self.messages
