# -*- coding: utf-8 -*-
from peewee import *

from model.basemodel import BaseModel


class User(BaseModel):
    id = PrimaryKeyField()
    insurance_id = IntegerField()
    telegram_id = IntegerField()
    facebook_id = IntegerField()


