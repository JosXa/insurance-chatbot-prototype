# -*- coding: utf-8 -*-
from appglobals import db
from peewee import *


class BaseModel(Model):
    class Meta:
        database = db
