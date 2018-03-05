from typing import List

import pytest

from corpus.questions import Questionnaire
from corpus import (
    all_questions,  # type: List[Question]
    Question,
    all_questionnaires  # type: List[Questionnaire]
)


def test_all_question_examples_are_valid():
    for q in all_questions:
        assert q.is_valid(q.example)
