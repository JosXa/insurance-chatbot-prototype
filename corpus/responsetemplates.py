import random
from pprint import pprint
from typing import Dict

from jinja2 import Environment, PackageLoader

from corpus import raw_templates
from model import User

env = Environment(
    loader=PackageLoader('corpus', 'templates'),
)


def format_intent(identifier):
    return identifier.lower().replace(' ', '_')


class TemplateRenderer(object):
    def __init__(self, user: User):
        self.user = user

    def _render_template(self, template, parameters=None, recursive=True):

        standard_parameters = {
            'user': self.user,
            'formal': self.user.formal_address,
            'informal': not self.user.formal_address
        }
        render_parameters = standard_parameters.copy()
        if parameters:
            render_parameters.update(parameters)

        rendered = template.render(**render_parameters)

        if recursive:
            to_rerender = env.from_string(rendered)
            rendered = to_rerender.render(**standard_parameters)
        return rendered.strip()

    def load_and_render(self,
                        intent: str,
                        parameters=None,
                        template_selector: 'SelectiveTemplateLoader' = None,
                        safe=False
                        ):
        if template_selector is None:
            template_selector = SelectiveTemplateLoader(None)

        response_template = template_selector.select(intent)

        try:
            return self._render_template(response_template.text_template, parameters)
        except Exception as e:
            if safe:
                return self.render_string(intent, parameters)
            else:
                raise e

    def render_string(self, template_str, parameters=None, recursive=True):
        template = env.from_string(template_str)
        return self._render_template(template, parameters, recursive=recursive)


class ResponseTemplate:
    def __init__(self, text):
        self.text_template = env.from_string(text)
        self.is_conjunction = False
        self.condition_template = None

    def check_condition(self, selection_context):
        if not self.condition_template:
            return True
        rendered = self.condition_template.render(**selection_context)
        return bool(eval(str(rendered)))

    @classmethod
    def from_metadata(cls, metadata):
        if isinstance(metadata, dict):
            obj = cls(metadata.get('text'))

            condition = metadata.get('condition')
            if condition:
                obj.condition_template = env.from_string(metadata['condition'])

            obj.is_conjunction = metadata.get('conjunction', False) or metadata.get('is_conjunction', False)

        elif isinstance(metadata, str):
            return cls(metadata)
        elif isinstance(metadata, list):
            raise NotImplementedError()
        else:
            raise ValueError(f"Unexpected format for metadata: {type(metadata)}")


class SelectiveTemplateLoader:
    def __init__(self, selection_context: Dict):
        if selection_context:
            self.selection_context = selection_context
        else:
            self.selection_context = dict()

    def _select_best_template(self, intent: str) -> ResponseTemplate:
        intent = format_intent(intent)
        candidate_templates = get_candidate_templates_by_id(intent)

        if not candidate_templates:
            raise NoViableTemplateFoundError(f"No template exists with intent '{intent}'.")

        if not isinstance(candidate_templates, list):
            candidate_templates = [candidate_templates]

        valid_candidates = [x for x in candidate_templates if x.check_condition(self.selection_context)]

        if len(valid_candidates) == 0:
            raise NoViableTemplateFoundError("No template fits the constraints.")

        return random.choice(valid_candidates)

    def select(self, intent: str) -> ResponseTemplate:
        return self._select_best_template(intent)


class NoViableTemplateFoundError(Exception):
    pass


def load_templates(raw):
    result = {}
    for k, v in raw.items():
        if isinstance(v, dict):
            for metadata in v['choices']:
                result.setdefault(k, []).append(ResponseTemplate.from_metadata(metadata))
        else:
            result[k] = ResponseTemplate.from_metadata(v)
    return result


all_response_templates = load_templates(raw_templates)


def get_candidate_templates_by_id(identifier):
    return all_response_templates.get(identifier.lower(), None)


if __name__ == '__main__':
    tmp = TemplateRenderer(user=User(formal_address=False))

    # pprint(all_response_templates)
    print(tmp.load_and_render("what i can do"))
