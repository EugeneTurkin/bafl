from enum import Enum


class HTML:
    class InputValue(Enum):
        YES = "true"


class Status(Enum):
    PENDING = "в обработке"
    ACCEPTED = "подтверждён"
    COMPLETED = "успех"
    FAILED = "ошибка"


class BadExtensions(Enum):
    JS = ".js"
    LNK = ".lnk"

    @classmethod
    def values(cls):
        return [enum.value for enum in list(cls)]
