import datetime
from enum import Enum
from typing import List

from model import User


class Separator(Enum):
    PARAGRAPH = '\n\n'
    LINE_BREAK = '\n'
    PUNCTUATION = ' '
    BUT = ', aber '


class ChatAction:
    class Type(Enum):
        ASKING_QUESTION = 0
        SAYING = 1
        SENDING_MEDIA = 2

    class Delay(Enum):
        SHORT = 1.2
        MEDIUM = 1.5
        LONG = 1.8

    def __init__(self,
                 action_type: Type,
                 peer: User,
                 text: str = None,
                 intents: List[str] = None,
                 media_id: str = None,
                 choices: List = None,
                 show_typing: bool = True,
                 delay: Delay = Delay.MEDIUM):
        self.action_type = action_type
        self.intents = intents
        self.choices = choices
        self.text_parts = [text]
        self.media_id = media_id
        self.peer = peer
        self.show_typing = show_typing
        self.delay = delay
        self.date = datetime.datetime.now()

    def render(self) -> str:
        return self.__str__()

    def __str__(self):
        return "".join([x for x in self.text_parts if x])
