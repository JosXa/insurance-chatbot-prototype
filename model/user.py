# -*- coding: utf-8 -*-
import os
from peewee import *

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

    @property
    def media_folder(self):
        path = os.path.join('files', str(self.id), 'media')
        if not os.path.exists(path):
            os.makedirs(path)
        return path
