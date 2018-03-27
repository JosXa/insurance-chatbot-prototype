import os

from jinja2 import Environment, PackageLoader

import util

PATH = os.path.split(os.path.abspath(__file__))[0]

env = Environment(
    loader=PackageLoader('corpus', 'templates'),
)

_TEMPLATES_DIR = 'templates'
_files = os.listdir(os.path.join(PATH, _TEMPLATES_DIR))
_yml_files = [x for x in _files if os.path.splitext(x)[1] in ('.yml', '.yaml')]

# Construct ResponseTemplate objects
raw_templates = dict()
for yml_file in _yml_files:
    loaded_yml = util.load_yaml_as_dict(os.path.join(PATH, _TEMPLATES_DIR, yml_file))
    if loaded_yml:
        raw_templates.update(loaded_yml)
