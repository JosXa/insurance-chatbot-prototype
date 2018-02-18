from typing import TypeVar

from fbmq import Event as FacebookEvent
from peewee import *
from telegram import Update as TelegramUpdate

from model import User
from model.basemodel import BaseModel

MessageUnderstanding = TypeVar('MessageUnderstanding')


class Update(BaseModel):
    user = ForeignKeyField(User)  # type: User
    client_name = CharField()  # type: str
    message_text = TextField()  # type: str
    message_id = CharField()  # type: str
    datetime = DateTimeField()  # type: datetime
    payload = CharField(null=True)  # type: str

    def __init__(self, *args, **kwargs):
        self.original_update = None  # type: [FacebookEvent,TelegramUpdate]
        self._understanding = None  # type: MessageUnderstanding
        self.voice_id = None  # type: str

        super().__init__(*args, **kwargs)

    @property
    def understanding(self) -> MessageUnderstanding:
        return self._understanding

    @understanding.setter
    def understanding(self, value: MessageUnderstanding):
        self._understanding = value
