# -*- coding: utf-8 -*-
from peewee import *

from model.basemodel import BaseModel
from telegram import User as TelegramUser


class User(BaseModel):
    id = PrimaryKeyField()
    insurance_id = IntegerField(null=True)
    telegram_id = IntegerField(null=True)
    facebook_id = IntegerField(null=True)

