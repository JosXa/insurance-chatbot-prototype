from typing import List

from fbmq import Event as FacebookEvent
from telegram import Update as TelegramUpdate

from model import User


class Update:
    def __init__(self):
        self.original_update = None  # type: [FacebookEvent,TelegramUpdate]
        self.client_name = None  # type: str
        self.user = None  # type: User
        self.message_text = None  # type: str
        self.message_id = None  # type: int

        self._intents = None  # type: List
        self._entities = None  # type: List
        self._parameters = None  # type: List

    @property
    def intents(self): return self._intents

    @intents.setter
    def intents(self, value): self._intents = value

    @property
    def entities(self): return self._entities

    @entities.setter
    def entities(self, value): self._entities = value

    @property
    def parameters(self): return self._parameters

    @parameters.setter
    def parameters(self, value): self._parameters = value
