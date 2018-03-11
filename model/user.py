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
    def name(self) -> str:
        return self.answers.get_answer('name')

    @property
    def media_folder(self):
        path = os.path.join('files', str(self.id), 'media')
        if not os.path.exists(path):
            os.makedirs(path)
        return path
