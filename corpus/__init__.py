import os
from pprint import pprint

import yaml
from jinja2 import Environment, PackageLoader

import utils
from corpus import questions

PATH = os.path.split(os.path.abspath(__file__))[0]

env = Environment(
    loader=PackageLoader('corpus', 'templates'),
)
all_questionnaires = questions.load_questionnaires()

response_templates = dict()

_TEMPLATES_DIR = 'templates'
_files = os.listdir(os.path.join(PATH, _TEMPLATES_DIR))
_yml_files = [x for x in _files if os.path.splitext(x)[1] in ('.yml', '.yaml')]

for yml_file in _yml_files:
    loaded_yml = utils.load_yaml_as_dict(os.path.join(PATH, _TEMPLATES_DIR, yml_file))
    response_templates.update(loaded_yml)

def get_template_by_id(identifier):
    try:
        return next(v for k, v in response_templates.items() if k.lower() == identifier.lower())
    except StopIteration:
        return None
