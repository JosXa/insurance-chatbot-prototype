import datetime
from typing import Set

from peewee import *

from model import User
from model.basemodel import BaseModel


class UserAnswers(BaseModel):
    NO_ANSWER = 'No data'

    datetime = DateTimeField()
    user = ForeignKeyField(User, related_name='answers')
    question_id = CharField()
    answer = TextField()

    @staticmethod
    def get_answered_question_ids(user: User) -> Set[int]:
        return {ua.question_id for ua in UserAnswers.select(UserAnswers.question_id).where(
            UserAnswers.user == user,
        )}

    @staticmethod
    def add_answer(user: User, question_id: str, answer: str):
        return UserAnswers.create(
            user=user,
            question_id=question_id,
            answer=answer,
            datetime=datetime.datetime.now()
        )

    @staticmethod
    def get_answer(user: User, question_id: str) -> str:
        try:
            return UserAnswers.select(
                UserAnswers.answer
            ).where(
                (UserAnswers.user == user) &
                (UserAnswers.question_id == question_id)
            ).order_by(
                -UserAnswers.datetime
            ).first().answer
        except UserAnswers.DoesNotExist:
            return None
