import random
from abc import ABCMeta, abstractmethod
from typing import Dict, List

from jinja2 import Environment, PackageLoader
from logzero import logger
from telegram.utils.helpers import escape_markdown

from corpus import emoji, raw_templates
from model import User
from utils import mutually_exclusive

env = Environment(
    loader=PackageLoader('corpus', 'templates'),
)

FORMATTING_PARAMS = {
    'bold': lambda s: f"*{escape_markdown(s)}*",
    'italic': lambda s: f"_{escape_markdown(s)}_",
    'code': lambda s: f"`{escape_markdown(s)}`",
    'escape': lambda s: escape_markdown(s)
}


def format_intent(identifier):
    return identifier.lower().replace(' ', '_')


class TemplateRenderer(object):
    def __init__(self, rendering_parameters):
        self.parameters = rendering_parameters

    def render_template(self, template, parameters=None, recursive=True):
        # merge shared parameter dicts
        render_parameters = {**self.parameters, **(parameters or {})}

        rendered = template.render(**render_parameters)

        if recursive:
            to_rerender = env.from_string(rendered)
            rendered = to_rerender.render(**render_parameters)
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
            return self.render_template(response_template.text_template, parameters)
        except Exception as e:
            if safe:
                return self.render_string(intent, parameters)
            else:
                raise e

    def render_string(self, template_str, parameters=None, recursive=True):
        template = env.from_string(template_str)
        return self.render_template(template, parameters, recursive=recursive)


class ResponseTemplate:
    PROPERTIES = ['prefix', 'suffix', 'conjunction']

    def __init__(self, intent, text):
        if not text:
            raise ValueError("Empty response templates make no sense.")
        self.intent = intent
        self.original_text = text
        self.text_template = env.from_string(emoji.replace_aliases(text))
        self.is_conjunction = False
        self.is_prefix = False
        self.is_suffix = False
        self.condition_template = None

    def check_condition(self, selection_context):
        if not self.condition_template:
            return True
        try:
            rendered = self.condition_template.render(**selection_context)
            return bool(eval(str(rendered)))
        except Exception as e:
            logger.error(f"Error while rendering condition of '{self.original_text}': {e}")
            return False

    @classmethod
    def from_metadata(cls, intent, choice, metadata=None):
        if isinstance(choice, dict):
            if not metadata:
                metadata = {}
            # TODO: refactor

            obj = cls(intent, choice.get('text'))

            condition = choice.get('condition')
            if condition:
                obj.condition_template = env.from_string(choice['condition'])

            for prop in ResponseTemplate.PROPERTIES:
                setattr(obj, 'is_' + prop, metadata.get(prop, False) in [True, 'yes'] or metadata.get(
                    'is_' + prop, False) in [True, 'yes'])

            if obj.is_suffix and obj.is_prefix:
                raise ValueError("Template cannot be suffix and prefix at the same time.")
            if obj.is_conjunction and any((obj.is_suffix, obj.is_prefix)):
                raise ValueError("A conjunction template cannot be suffix or prefix.")
            if not obj.is_prefix and not obj.is_conjunction:
                obj.is_suffix = True

            # Assert 'is_'-values are mutually exclusive
            if not mutually_exclusive([getattr(obj, 'is_' + prop) for prop in ResponseTemplate.PROPERTIES]):
                raise ValueError("Template properties need to be mutually exclusive.")

            return obj
        elif isinstance(choice, str):
            return cls(intent, choice)
        elif isinstance(intent, choice, list):
            raise NotImplementedError()
        else:
            raise ValueError(f"Unexpected format for metadata: {type(choice)}")


class TemplateSelector(metaclass=ABCMeta):
    @abstractmethod
    def select_template(self, candidates: List[ResponseTemplate]) -> ResponseTemplate: pass


class RandomTemplateSelector(TemplateSelector):
    def select_template(self, candidates: List[ResponseTemplate]) -> ResponseTemplate:
        return random.choice(candidates)


# class OccurenceTemplateSelector(TemplateSelector):
#     def __init__(self, user):
#         self.counter = {}
#
#     def select_template(self, candidates: List[ResponseTemplate]):
#         least_used = list()
#         min_value = 0
#         for c in candidates:
#             if c in self.counter and self.counter[c] > min_value:
#                 continue
#             least_used.append(c)
#         result = random.choice(least_used)
#         self.counter[result] = self.counter.setdefault(result, 0) + 1
#         return result


class SelectiveTemplateLoader:
    def __init__(self, selection_context: Dict, template_selector: TemplateSelector = None):
        if selection_context:
            self.selection_context = selection_context
        else:
            self.selection_context = dict()

        if not template_selector:
            template_selector = RandomTemplateSelector()
        self.template_selector = template_selector

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

        return self.template_selector.select_template(valid_candidates)

    def select(self, intent: str) -> ResponseTemplate:
        return self._select_best_template(intent)


class NoViableTemplateFoundError(Exception):
    pass


def load_templates(raw):
    result = {}
    for k, v in raw.items():
        try:
            if isinstance(v, dict):
                metadata = {k: v for k, v in v.items() if k not in ('choices', 'text')}
                if v.get('choices'):
                    # Parse all choices
                    for choice in v['choices']:
                        result.setdefault(k, []).append(ResponseTemplate.from_metadata(k, choice, metadata))
                else:
                    # No choices, just an uppermost-level dict
                    result[k] = ResponseTemplate.from_metadata(k, v, metadata)
            else:
                result[k] = ResponseTemplate.from_metadata(k, v)
        except Exception as e:
            print('error')
            logger.warning(f"Error parsing the template of intent {k}: {v}")
            logger.exception(e)

    # Sanity checks
    assert not any(k is None or v is None for k, v in result.items()), "There are None values"

    return result


all_response_templates = load_templates(raw_templates)


def get_candidate_templates_by_id(identifier):
    return all_response_templates.get(identifier.lower(), None)


if __name__ == '__main__':
    tmp = TemplateRenderer(user=User(formal_address=False))

    # pprint(all_response_templates)
    print(tmp.load_and_render("start"))
