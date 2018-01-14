import random
from pprint import pprint
from typing import Union

from corpus import env, get_template_by_id
from corpus.questions import Question
from model import User


class TemplateRenderer(object):
    def __init__(self, user: User):
        self.user = user

    def _render_template_str(self, template, parameters=None):
        if isinstance(template, str):
            template = env.from_string(template)

        render_parameters = {
            'user': self.user,
            'formal': self.user.formal_address,
            'informal': not self.user.formal_address
        }
        if parameters:
            render_parameters.update(parameters)

        rendered = template.render(**render_parameters)
        return rendered.strip()

    def load_and_render(self,
                        intent: str,
                        parameters=None,
                        template_selector: 'TemplateSelector' = None):
        if template_selector is None:
            template_selector = TemplateSelector()

        template_str = template_selector.select(intent)

        return self.render_string(template_str, parameters)

    def render_string(self, template_str, parameters=None):
        return self._render_template_str(template_str, parameters)


class TemplateSelector:
    def __init__(self, questionnaire_completion: float = None, politeness: float = None):
        # TODO: perhaps make this a dynamically-valued (strings) dict?
        self.questionnaire_completion = questionnaire_completion
        self.politeness = politeness

    def select(self, intent):
        intent = intent.replace(' ', '_')
        responses_obj = get_template_by_id(intent)
        viable_choices = list()

        if not responses_obj:
            raise NoViableTemplateFoundError("No template with the intent '{}' exists.".format(
                intent))

        if isinstance(responses_obj, str):
            viable_choices.append(responses_obj)
        elif isinstance(responses_obj, dict):
            choices_obj = responses_obj.get('choices', None)

            if choices_obj is not None:
                # FIXME: not pretty
                for c in choices_obj:
                    if isinstance(choices_obj, dict):
                        completion_obj = c.get('min_completion')
                        if self.questionnaire_completion and completion_obj.get('questionnaire'):
                            if self.questionnaire_completion > completion_obj['questionnaire']:
                                viable_choices.append(c.get('text'))
                        else:
                            viable_choices.append(c.get('text'))
                    elif isinstance(choices_obj, list):
                        for c in choices_obj:
                            viable_choices.append(c)
                    else:
                        raise ValueError("unexpected format")
            else:
                viable_choices.append("test")

        if len(viable_choices) == 0:
            raise NoViableTemplateFoundError("No template fits the constraints.")
        return random.choice(viable_choices)


class NoViableTemplateFoundError(Exception):
    pass


if __name__ == '__main__':
    tmp = TemplateRenderer(user=User(formal_address=False))

    print(tmp.load_and_render("what i can do"))
