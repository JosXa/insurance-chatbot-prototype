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

        self._intents = None  # type: List
        self._entities = None  # type: List
        self._parameters = None  # type: List

    @classmethod
    def from_telegram_update(cls, update: TelegramUpdate):
        obj = cls()
        obj.original_update = update
        obj.client_name = 'telegram'

        obj.user, created = User.get_or_create(telegram_id=update.effective_user.id)
        if created:
            obj.user.save()
        obj.message_text = update.effective_message.text
        return obj

    @classmethod
    def from_facebook_event(cls, event: FacebookEvent):
        pass

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
