import os
import random
import re
import traceback
from pprint import pprint
from typing import Iterable, List

import itertools
from logzero import logger as log

import utils
from corpus import conditions
from corpus.responsetemplates import env

PATH = os.path.split(os.path.abspath(__file__))[0]
QUESTIONNAIRE_FILE = os.path.join(PATH, 'questionnaires.yml')


class Question:
    def __init__(self,
                 qid,
                 title,
                 is_required,
                 condition: str = None,
                 confirm: str = None,
                 implicit_grounding: str = None,
                 choices: List = None,
                 hint=None,
                 example=None,
                 match_regex=None,
                 media=False):
        if media and any((confirm, choices, match_regex)):
            raise ValueError("If the `media` argument is True, then `confirm`, `choices` and `match_regex` are "
                             "forbidden.")
        if confirm and implicit_grounding:
            raise ValueError("The `confirm` and `implicit_grounding` parameters are mutually exclusive.")
        self.id = qid
        self.title = title
        self.is_required = is_required
        self.condition_template = None if condition is None else env.from_string(condition)
        self.confirm = confirm
        self.implicit_grounding = implicit_grounding
        self.choices = choices
        self.match_regex = re.compile(match_regex) if match_regex else None
        self.hint = hint
        self.example = example
        self.media = media

    @classmethod
    def from_dict(cls, id, values: dict):
        return cls(
            qid=id,
            title=values['title'],
            is_required=values.get('required', False),
            condition=values.get('condition'),
            confirm=values.get('confirm'),
            implicit_grounding=values.get('implicit_grounding'),
            hint=values.get('hint'),
            choices=values.get('choices'),
            example=values.get('example'),
            match_regex=values.get('match_regex'),
            media=values.get('media')
        )

    def is_applicable(self, condition_context):
        try:
            return conditions.check_condition(self.condition_template, condition_context)
        except Exception as e:
            traceback.print_exc()
            log.error(f"Error while rendering condition of question '{self.title}': {e}")
            return False

    def is_valid(self, value):
        if self.match_regex:
            if not bool(self.match_regex.search(value)):
                return False
        if self.choices:
            if value.lower() not in (x.lower() for x in self.choices):
                return False
        return True

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

    def next_question(self, answered_question_ids: Iterable[str]) -> Question:
        try:
            return next(x for x in self.questions if x.id not in answered_question_ids)
        except StopIteration:
            return None

    def completion_ratio(self, answered_question_ids: Iterable[str]) -> Question:
        relevant_ids = [x.id for x in self.questions if x.id in answered_question_ids]
        return len(relevant_ids) / len(self.questions)

    def random_question(self, answered_question_ids: Iterable[str]) -> Question:
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


all_questionnaires = load_questionnaires()
all_questions = list(itertools.chain.from_iterable([x.questions for x in all_questionnaires]))


def get_question_by_id(identifier: str) -> Question:
    try:
        return next(x for x in all_questions if x.id == identifier.lower())
    except StopIteration:
        return None


if __name__ == '__main__':
    pprint(load_questionnaires())
