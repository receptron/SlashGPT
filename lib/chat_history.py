class ChatHistory:
    def __init__(self):
        self.__messages = []

    def append(self, data):
        self.__messages.append(data)


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

    def messages(self):
        return self.__messages
