import random
from abc import ABCMeta, abstractmethod
from typing import Dict, List

from logzero import logger as log
from telegram.utils.helpers import escape_markdown

from corpus import conditions, env, raw_templates
from corpus.emojis import emoji
from utils import mutually_exclusive

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

        # Add method to load and render response templates directly from the jinja2 template
        self.parameters.update(dict(
            render=lambda x: self.load_and_render(
                intent=x,
                parameters=self.parameters,
                template_loader=SelectiveTemplateLoader(
                    self.parameters,
                    RandomTemplateSelector()
                ),
                safe=True
            )
        ))

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
                        template_loader: 'SelectiveTemplateLoader' = None,
                        safe=False
                        ):
        if template_loader is None:
            template_loader = SelectiveTemplateLoader(None)

        response_template = None
        try:
            response_template = template_loader.select(intent)
        except NoViableTemplateFoundError:
            if not safe:
                raise

        if response_template:
            return self.render_template(response_template.text_template, parameters)
        return self.render_string(template_str=intent, parameters=parameters)

    def render_string(self, template_str, parameters=None, recursive=True):
        template = env.from_string(template_str)
        return self.render_template(template, parameters, recursive=recursive)


class ResponseTemplate:
    PROPERTIES = ['prefix', 'suffix', 'conjunction']

    def __init__(
            self,
            intent,
            text,
            is_conjunction=False,
            is_prefix=False,
            is_suffix=False,
            condition: str = None):
        if not text:
            raise ValueError("Empty response templates make no sense.")
        self.intent = intent
        self.original_text = text
        self.text_template = env.from_string(emoji.replace_aliases(text))
        self.is_conjunction = is_conjunction
        self.is_prefix = is_prefix
        self.is_suffix = is_suffix
        self._original_condition_str = condition
        self.condition_template = None if condition is None else env.from_string(condition)

    def check_condition(self, condition_context):
        try:
            return conditions.check_condition(self.condition_template, condition_context)
        except Exception as e:
            log.error(f"Error while rendering condition of '{self.original_text}': {e}")
            return False

    @classmethod
    def from_metadata(cls, intent, choice, metadata=None):
        if isinstance(choice, dict):
            if not metadata:
                metadata = {}

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

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"ResponseTemplate(intent={self.intent}, " \
               f"text={self.original_text}), " + \
               (f"is_conjunction=True, " if self.is_conjunction else "") + \
               (f"is_prefix=True, " if self.is_prefix else "") + \
               (f"is_suffix=True, " if self.is_suffix else "") + \
               (f"condition={self._original_condition_str}" if self._original_condition_str else "")


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
    def __init__(self, selection_context: Dict = None, template_selector: TemplateSelector = None):
        if selection_context:
            self.selection_context = selection_context
        else:
            self.selection_context = dict()

        if not template_selector:
            template_selector = RandomTemplateSelector()
        self.template_selector = template_selector

    def _select_best_template(self, intent: str) -> ResponseTemplate:
        intent = format_intent(intent)
        candidate_templates = get_templates_by_id(intent)

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
            log.warning(f"Error parsing the template of intent {k}: {v}")
            log.exception(e)

    # Sanity checks
    assert not any(k is None or v is None for k, v in result.items()), "There are None values"

    return result


all_response_templates = load_templates(raw_templates)


def get_templates_by_id(identifier):
    return all_response_templates.get(identifier.lower(), None)
