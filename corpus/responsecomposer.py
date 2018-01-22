import string
from typing import List, Union

from corpus import Question
from corpus.responsetemplates import SelectiveTemplateLoader, TemplateRenderer, format_intent
from logic import ChatAction
from logic.chataction import Separator
from model import User


class ResponseComposer:
    def __init__(self,
                 peer: User,
                 template_loader: SelectiveTemplateLoader):
        self.peer = peer
        self.loader = template_loader
        self.renderer = TemplateRenderer(user=self.peer)

        self._sequence = []  # type: List[ChatAction]

    def collect_actions(self) -> List[ChatAction]:
        return self._sequence

    def give_hint(self, question: Question):

        surrounding = self.loader.select('hint_surrounding')
        text = self.renderer.render_string(surrounding, {'question': question}, recursive=True)

        return self._create_action(text, 'give_hint')

    def _format_question_title(self, question: Question, parameters):
        surrounding = self.loader.select('question_surrounding')
        return self.renderer.render_string(surrounding, parameters, recursive=True)

    def _create_question_text(self,
                              question: Union[Question, str],
                              choices: List = None,
                              parameters=None):

        if choices and isinstance(question, Question):
            raise ValueError("Choices for Question objects must be defined in the questionnaire.yml and cannot be "
                             "provded as arguments.")

        default_question_params = dict(question=question)
        if parameters:
            parameters.update(default_question_params)
        else:
            parameters = default_question_params

        if isinstance(question, Question):
            text = self._format_question_title(question, parameters)
            choices = question.choices
        elif isinstance(question, str):
            text = self.renderer.load_and_render(intent=question, template_selector=self.loader, parameters=parameters)
        else:
            raise ValueError(f"Incompatible type of question: {type(question)}")

        if choices:
            choices = [self.renderer.load_and_render(x, safe=True) for x in choices]

        question_id = question.id if isinstance(question, Question) else question

    def ask(self,
            question: Union[Question, str],
            choices: List = None,
            parameters=None,
            ):

        return self._create_action(text,
                                   question_id,
                                   parameters=parameters,
                                   choices=choices,
                                   type_=ChatAction.Type.ASKING_QUESTION)

    def say(self, *intents, render_parameters=None):
        """
        Say something in a new message
        """
        first = True
        for intent in intents:
            if not intent:
                continue

            text = self.renderer.load_and_render(intent=intent, template_selector=self.loader,
                                                 parameters=render_parameters)
            self._create_action(text, intent, as_new_message=first)
            first = False

        return self

    def then_ask(self,
                 question: Union[Question, str],
                 choices: List = None,
                 parameters=None,
                 ):
        return self

    def _add_to_previous_element(self, intent, text, separator):
        # Append to previous message
        previous_action = self._sequence[-1]
        previous_action.intents.append(intent)

        if separator is None:
            separator = Separator.PUNCTUATION

        if separator == Separator.BUT:
            # Conjunction of sentence --> Lowercase
            text = text[0].lower() + text[1:]

        if separator == Separator.PUNCTUATION:
            previous_text_part = previous_action.text_parts[-1]

            # Append "." to last part if necessary
            if previous_text_part.strip()[-1] not in string.punctuation:
                previous_action.text_parts[-1] += '.'

        previous_action.text_parts.append(separator.value)
        previous_action.text_parts.append(text)

    def _create_action(self,
                       text,
                       intent,
                       choices: List = None,
                       separator: Separator = None,
                       type_: ChatAction.Type = ChatAction.Type.SAYING,
                       as_new_message=True,
                       ):

        intent = format_intent(intent)

        if as_new_message or len(self._sequence) == 0:
            # Create new message
            self._sequence.append(
                ChatAction(
                    type_,
                    peer=self.peer,
                    text=text,
                    intents=[intent],
                    choices=choices,
                    show_typing=True,
                    delay=ChatAction.Delay.MEDIUM))
        else:
            self._add_to_previous_element(intent, text, separator)
        return self

    def __str__(self):
        return ' then '.join(
            f"{'send' if x.action_type == ChatAction.Type.SAYING else 'ask'} {x.render()}"
            for x in self.collect_actions()
        )
