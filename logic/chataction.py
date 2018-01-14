import datetime
import string
from enum import Enum
from typing import List

from corpus.questions import Question
from corpus.responsetemplates import TemplateRenderer, TemplateSelector
from model import User


class ChatAction:
    class Type(Enum):
        ASKING_QUESTION = 0
        SAYING = 1

    class Delay(Enum):
        SHORT = 0.5
        MEDIUM = 1.2
        LONG = 2

    class TextPartSeparator(Enum):
        PARAGRAPH = '\n\n'
        LINE_BREAK = '\n'
        PUNCTUATION = ' '

    def __init__(self,
                 action_type: Type,
                 peer: User, text: str,
                 intents: List[str],
                 show_typing: bool = True,
                 delay: Delay = Delay.MEDIUM):
        self.action_type = action_type
        self.intents = intents
        self.text_parts = [text]
        self.peer = peer
        self.show_typing = show_typing
        self.delay = delay
        self.date = datetime.datetime.now()

    def render(self) -> str:
        return self.__str__()

    def __str__(self):
        return "".join(self.text_parts)


class ChatActionsBuilder:
    def __init__(self,
                 peer: User,
                 template_selector: TemplateSelector):
        self.peer = peer
        self.selector = template_selector
        self.renderer = TemplateRenderer(user=self.peer)

        self._sequence = []  # type: List[ChatAction]

    def collect_actions(self):
        return self._sequence

    def say(self,
            intent,
            parameters=None,
            show_typing: bool = True,
            delay: ChatAction.Delay = None,
            separator: ChatAction.TextPartSeparator = None,
            **kwargs
            ):

        text = self.renderer.load_and_render(intent=intent, parameters=parameters, template_selector=self.selector)

        return self._create_action(text, intent, parameters=parameters, show_typing=show_typing, delay=delay,
                                   separator=separator, **kwargs)

    def ask(self,
            question: Question,
            parameters=None,
            show_typing: bool = True,
            delay: ChatAction.Delay = None,
            separator: ChatAction.TextPartSeparator = ChatAction.TextPartSeparator.PARAGRAPH,
            **kwargs
            ):
        question_title = question.title
        text = self.renderer.render_string(question_title, parameters)

        return self._create_action(text, question.id, parameters=parameters, show_typing=show_typing, delay=delay,
                                   separator=separator, **kwargs)

    def then_say(self,
                 intent,
                 parameters=None,
                 show_typing: bool = True,
                 delay: ChatAction.Delay = ChatAction.Delay.MEDIUM):
        self.say(intent, parameters, show_typing, delay, new_message=False)
        return self

    def then_ask(self,
                 question: Question,
                 parameters=None,
                 show_typing: bool = True,
                 delay: ChatAction.Delay = ChatAction.Delay.MEDIUM):
        self.ask(question, parameters, show_typing, delay, new_message=False)
        return self

    def _add_to_previous_element(self, intent, text, separator):
        # Append to previous message
        previous_action = self._sequence[-1]

        previous_action.intents.append(intent)

        if separator is None:
            separator = ChatAction.TextPartSeparator.PUNCTUATION

        if separator == ChatAction.TextPartSeparator.PUNCTUATION:
            previous_text_part = previous_action.text_parts[-1]

            # Append "." to last part if necessary
            if not previous_text_part[-1] in string.punctuation:
                previous_text_part += '.'

        previous_action.text_parts.append(separator.value)
        previous_action.text_parts.append(text)

    def _create_action(self,
                       text,
                       intent,
                       parameters=None,
                       show_typing: bool = True,
                       delay: ChatAction.Delay = None,
                       separator: ChatAction.TextPartSeparator = None,
                       **kwargs
                       ):

        if 'new_message' in kwargs or len(self._sequence) == 0:
            # Create new message
            self._sequence.append(
                ChatAction(
                    ChatAction.Type.SAYING,
                    peer=self.peer,
                    text=text,
                    intents=[intent],
                    show_typing=show_typing,
                    delay=delay))
        else:
            self._add_to_previous_element(intent, text, separator)

        return self
