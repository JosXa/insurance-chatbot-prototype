import os
import random
import re
from pprint import pprint
from typing import List

import utils

PATH = os.path.split(os.path.abspath(__file__))[0]
QUESTIONNAIRE_FILE = os.path.join(PATH, 'questionnaires.yml')


class Question:
    def __init__(self, qid, title, is_required, choices: List = None, hint=None, example=None, match_regex=None):
        self.id = qid
        self.title = title
        self.is_required = is_required
        self.choices = choices
        self.match_regex = re.compile(match_regex) if match_regex else None
        self.hint = hint
        self.example = example

    @classmethod
    def from_dict(cls, id, values: dict):
        return cls(
            qid=id,
            title=values['title'],
            is_required=values.get('required', False),
            hint=values.get('hint'),
            choices=values.get('choices'),
            example=values.get('example'),
            match_regex=values.get('match_regex')
        )

    def is_valid(self, value):
        result = True
        if self.match_regex:
            result = bool(self.match_regex.match(value))
        # more to come
        return result

    def __repr__(self):
        return 'Question("{self.id}", "{self.title}", hint="{self.hint}", example=' \
               '"{self.example}", match_regex={self.match_regex})'.format(self=self)


class Questionnaire:
    def __init__(self, qid: str, title: str, questions: List[Question]):
        self.id = qid
        self.title = title
        self.questions = questions

    def is_first_question(self, question: Question) -> bool:
        return self.questions.index(question) == 0

    def next_question(self, answered_question_ids: List[str]) -> Question:
        try:
            return next(x for x in self.questions if x.id not in answered_question_ids)
        except StopIteration:
            return None

    def completion_ratio(self, answered_question_ids: List[str]) -> Question:
        relevant_ids = [x.id for x in self.questions if x.id in answered_question_ids]
        return len(relevant_ids) / len(self.questions)

    def random_question(self, answered_question_ids: List[str]) -> Question:
        all_unanswered = [x for x in self.questions if x.id not in answered_question_ids]
        return random.choice(all_unanswered)

    @classmethod
    def from_dict(cls, id, values) -> 'Questionnaire':
        return cls(
            qid=id,
            title=values['title'],
            questions=[Question.from_dict(k, v) for k, v in values['questions'].items()]
        )

    def __repr__(self):
        return 'Questionnaire("{self.id}", "{self.title}", questions={self.questions}'.format(
            self=self)


def load_questionnaires():
    q_dict = utils.load_yaml_as_dict(QUESTIONNAIRE_FILE)
    questionnaires = [Questionnaire.from_dict(k, v) for k, v in q_dict.items()]
    assert are_question_ids_unique(questionnaires)
    return questionnaires


def are_question_ids_unique(questionnaires: List[Questionnaire]) -> bool:
    ids = list()
    for q in questionnaires:
        if q.id in ids:
            return False
        else:
            ids.append(q.id)
    return True


if __name__ == '__main__':
    pprint(load_questionnaires())
