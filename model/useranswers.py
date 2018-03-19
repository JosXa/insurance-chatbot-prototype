import datetime
from typing import Set

from mwt import mwt
from peewee import *

from model import User
from model.basemodel import BaseModel


class UserAnswers(BaseModel):
    NO_ANSWER = 'No data'

    datetime = DateTimeField()
    user = ForeignKeyField(User, related_name='answers')
    question_id = CharField()
    answer = TextField()

    # cannot_answer = BooleanField(default=False)
    # will_not_answer = BooleanField(default=False)

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
    @mwt(timeout=2)
    def get_answer(user: User, question_id: str) -> str:
        """
        Queries for the most recent answer to the given `question_id`.
        If `safe` is `True`, returns `None` even if the `NO_ANSWER` flag is set.
        """
        try:
            val = UserAnswers.select(
                UserAnswers.answer
            ).where(
                (UserAnswers.user == user) &
                (UserAnswers.question_id == question_id)
            ).order_by(
                -UserAnswers.datetime
            ).first()
            if val:
                return val.answer
            return None
        except UserAnswers.DoesNotExist:
            return None

    @staticmethod
    @mwt(timeout=2)
    def has_answered(user: User, question_id: str):
        ans = UserAnswers.get_answer(user, question_id)
        return ans is not None and ans != UserAnswers.NO_ANSWER
