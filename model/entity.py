from typing import Iterable


class BaseEntity:
    def __init__(self, type, choices: Iterable = None):
        self.type = type
        if choices is not None:
            if not all(isinstance(x, self.type) for x in choices):
                raise ValueError("All choices must be of the same type.")
        self.choices = choices
        self.value = None

    def validate(self, value) -> bool:
        if not isinstance(value, self.type):
            return False

        if self.choices is not None:
            return value in self.choices
        return True


class NameEntity(BaseEntity):
    def __init__(self):
        super(NameEntity, self).__init__(
            type=str
        )

class PhoneNumberEntity(BaseEntity):
    def __init__(self, ):
        super(PhoneNumberEntity, self).__init__(
            type=int
        )

    def __str__(self):
        pass

