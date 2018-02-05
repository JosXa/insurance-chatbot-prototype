from typing import Set

from peewee import *

from model import User
from model.basemodel import BaseModel


class UserAnswers(BaseModel):
    NO_ANSWER = 'No data'

    user = ForeignKeyField(User)
    question_id = CharField()
    answer = TextField()

    @staticmethod
    def get_answered_question_ids(user: User) -> Set[int]:
        return {ua.question_id for ua in UserAnswers.select(UserAnswers.question_id).where(
            UserAnswers.user == user,
        )}
