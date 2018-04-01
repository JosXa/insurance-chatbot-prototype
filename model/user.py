# -*- coding: utf-8 -*-
import os
from peewee import *

from appglobals import ROOT_DIR
from model.basemodel import BaseModel


class User(BaseModel):
    id = PrimaryKeyField()
    insurance_id = IntegerField(null=True)
    telegram_id = IntegerField(null=True)
    facebook_id = CharField(null=True)

    formal_address = BooleanField(default=True)

    @staticmethod
    def merge_same_user(user1: 'User', user2: 'User') -> 'User':
        pass  # TODO

    @property
    def name(self) -> str:  # Displayname
        return self.first_name

    @property
    def first_name(self) -> str:
        from model import UserAnswers
        return UserAnswers.get_answer(self, 'first_name')

    @property
    def last_name(self) -> str:
        from model import UserAnswers
        return UserAnswers.get_answer(self, 'last_name')

    @first_name.setter
    def first_name(self, value):
        from model import UserAnswers
        UserAnswers.add_answer(user=self, question_id='first_name', answer=value)

    @last_name.setter
    def last_name(self, value):
        from model import UserAnswers
        UserAnswers.add_answer(user=self, question_id='last_name', answer=value)

    def get_media_folder(self, create=True):
        return _create_folder("media", self.id, create)

    def get_recording_folder(self, create=True):
        return _create_folder("recordings", self.id, create)

    def __str__(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name} ({self.id})"
        elif self.first_name:
            return f"{self.first_name} ({self.id})"
        else:
            return f"User(id={self.id})"


def _create_folder(name, user_id, create=True):
    path = os.path.join(ROOT_DIR, 'tmp', str(user_id), name)
    if create:
        if not os.path.exists(path):
            os.makedirs(path)
    return path
