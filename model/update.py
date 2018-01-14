from datetime import datetime
from typing import List

from fbmq import Event as FacebookEvent
from telegram import Update as TelegramUpdate

from clients.nlpclients import MessageUnderstanding
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
        self._understanding = None  # type: MessageUnderstanding

        super().__init__(*args, **kwargs)

    @property
    def understanding(self):
        return self._understanding

    @understanding.setter
    def understanding(self, value):
        self._understanding = value
