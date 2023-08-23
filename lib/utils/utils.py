from enum import Enum


class InputStyle(Enum):
    HELP = 1
    TALK = 2
    SLASH = 3
    SAMPLE = 4


class CALL_TYPE(Enum):
    REST = 1
    GRAPHQL = 2
    DATA_URL = 3
    MESSAGE_TEMPLATE = 4
