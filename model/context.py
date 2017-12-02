from peewee import *

from model import User
from model.basemodel import BaseModel


class Context(BaseModel):
    user = ForeignKeyField(User)


