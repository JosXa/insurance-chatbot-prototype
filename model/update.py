from datetime import datetime
from typing import List

from fbmq import Event as FacebookEvent
from telegram import Update as TelegramUpdate

from model import User
from model.basemodel import BaseModel
from peewee import *


class Update(BaseModel):
    user = ForeignKeyField(User)  # type: User
    client_name = CharField()  # type: str
    message_text = TextField()  # type: str
    message_id = IntegerField()  # type: int
    datetime = DateTimeField()  # type: datetime

    def __init__(self, *args, **kwargs):
        self.original_update = None  # type: [FacebookEvent,TelegramUpdate]

        self._intents = None  # type: List
        self._contexts = None  # type: List
        self._parameters = None  # type: List
        super().__init__(*args, **kwargs)

    @property
    def intents(self): return self._intents

    @intents.setter
    def intents(self, value): self._intents = value

    @property
    def contexts(self): return self._contexts

    @contexts.setter
    def contexts(self, value): self._contexts = value

    @property
    def parameters(self): return self._parameters

    @parameters.setter
    def parameters(self, value): self._parameters = value
