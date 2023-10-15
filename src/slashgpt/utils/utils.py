from enum import Enum


class InputStyle(Enum):
    HELP = 1
    TALK = 2
    SLASH = 3
    SAMPLE = 4


class CallType(Enum):
    REST = 1
    GRAPHQL = 2
    DATA_URL = 3
    MESSAGE_TEMPLATE = 4
    EMIT = 5
    DEBUG = 6

    @classmethod
    def withKey(cls, value):
        value = value.upper()
        for member in cls:
            if member.name == value:
                return member
        return None


COLOR_DEBUG = "cyan"
COLOR_INFO = "blue"
COLOR_WARNING = "yellow"
COLOR_ERROR = "red"

if __name__ == "__main__":
    assert CallType.withKey("rest") == CallType.REST
    assert CallType.withKey("bar") is None
