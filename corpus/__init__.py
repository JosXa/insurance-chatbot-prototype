import itertools
import os

import utils
from corpus import questions
from corpus.questions import Question

PATH = os.path.split(os.path.abspath(__file__))[0]

all_questionnaires = questions.load_questionnaires()
all_questions = list(itertools.chain.from_iterable([x.questions for x in all_questionnaires]))

_TEMPLATES_DIR = 'templates'
_files = os.listdir(os.path.join(PATH, _TEMPLATES_DIR))
_yml_files = [x for x in _files if os.path.splitext(x)[1] in ('.yml', '.yaml')]

# Construct ResponseTemplate objects
raw_templates = dict()
for yml_file in _yml_files:
    loaded_yml = utils.load_yaml_as_dict(os.path.join(PATH, _TEMPLATES_DIR, yml_file))
    raw_templates.update(loaded_yml)


def get_question_by_id(identifier: str) -> Question:
    try:
        return next(x for x in all_questions if x.id == identifier.lower())
    except StopIteration:
        return None
