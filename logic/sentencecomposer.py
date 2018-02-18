import string
from typing import List, Union

from core import ChatAction
from corpus import Question
from corpus.responsetemplates import ResponseTemplate, SelectiveTemplateLoader, TemplateRenderer, format_intent
from model import User


class SentenceComposer:
    def __init__(self,
                 peer: User,
                 template_loader: SelectiveTemplateLoader,
                 template_renderer: TemplateRenderer
                 ):
        self.peer = peer
        self.loader = template_loader
        self.renderer = template_renderer

        self._sequence = []  # type: List[ChatAction]
        self._inside_conjunction = False

    def collect_actions(self) -> List[ChatAction]:
        return self._sequence

    def give_hint(self, question: Question):
        surrounding = self.loader.select('hint_surrounding')
        text = self.renderer.render_template(surrounding.text_template, {'question': question}, recursive=True)

        return self._create_action('give_hint', text)

    def give_example(self, question: Question):
        prefix = self.renderer.load_and_render('example')
        suffix = self.renderer.render_string(question.example)

        return self._create_action('give_example', f"{prefix} {suffix}")

    def ask(self,
            question: Union[Question, str],
            choices: List = None,
            parameters=None,
            ):
        return self._create_question(question, choices, parameters, as_new_message=False)

    def say(self, *intents, parameters=None):
        """
        Say something in a new message
        """
        first = True
        for intent in intents:
            if not intent:
                continue

            template = self.loader.select(intent)
            text = self.renderer.render_template(template.text_template, parameters=parameters)

            self._create_action(intent, text, template, as_new_message=first)
            first = False

        return self

    def then_ask(self,
                 question: Union[Question, str],
                 choices: List = None,
                 parameters=None,
                 ):
        return self._create_question(question, choices, parameters, as_new_message=True)

    def ask_to_confirm(self,
                       question: Question,
                       user_answer: str):
        text = self.renderer.render_string(question.confirm, parameters={'answer': user_answer, 'question': question})
        self._create_action('confirm_answer', text)
        self.ask('is that correct', choices=['affirm_correct', 'negate_wrong'])
        return self

    def send_media(self, media_id, caption_intent=None, parameters=None):
        media_id = format_intent(media_id)
        text = None
        if caption_intent:
            template = self.loader.select(caption_intent)
            text = self.renderer.render_template(template.text_template, parameters=parameters)

        self._create_action(
            caption_intent or media_id,
            text,
            media_id=media_id,
            type_=ChatAction.Type.SENDING_MEDIA,
            as_new_message=True
        )
        return self

    def _append_to_previous(self, intent, text, template: ResponseTemplate = None, choices=None):
        # Append to previous message

        previous_action = self._sequence[-1]
        previous_action.intents.append(intent)

        if choices:
            previous_action.choices = choices

        def finish_last_sentence(value: ChatAction):
            last_part = value.text_parts[-1]
            last_char = last_part[-1]
            if last_char not in string.punctuation and last_char != ' ':
                last_part[-1] = last_part[-1] + '.'

        separator = '. '

        if (template and template.is_conjunction) or self._inside_conjunction:
            separator = ''
            text = text[0].lower() + text[1:]
            self._inside_conjunction = False

        if template is not None:
            if template.is_conjunction:
                if previous_action.text_parts[-1][-1] in string.punctuation:
                    raise ValueError("Trying to append a conjunction to a sentence with punctuation.")
                # Append space if necessary
                if text[-1] not in string.punctuation and text[-1] != ' ':
                    text = text + ' '
                self._inside_conjunction = True
            elif template.is_prefix:
                finish_last_sentence(previous_action)
                # Uppercase
                text = text[0].upper() + text[1:]
                separator = ' '
                self._inside_conjunction = False
            elif template.is_suffix:
                separator = ' '
                self._inside_conjunction = True

        previous_action.text_parts.append(separator)
        previous_action.text_parts.append(text)

    def _create_action(self,
                       intent,
                       text,
                       media_id: str = None,
                       response_template: ResponseTemplate = None,
                       choices: List = None,
                       type_: ChatAction.Type = ChatAction.Type.SAYING,
                       as_new_message=True,
                       ):
        if choices and any(x.choices for x in self._sequence):
            raise ValueError("Multiple messages with choices are not sensible.")

        intent = format_intent(intent)

        delay = None  # If empty sequence
        if len(self._sequence) == 1:
            delay = ChatAction.Delay.SHORT
        elif len(self._sequence) >= 3:
            delay = ChatAction.Delay.LONG
        elif len(self._sequence) > 0:
            delay = ChatAction.Delay.MEDIUM

        if as_new_message or len(self._sequence) == 0:
            # Create new message
            self._sequence.append(
                ChatAction(
                    type_,
                    peer=self.peer,
                    text=text,
                    intents=[intent],
                    media_id=media_id,
                    choices=choices,
                    show_typing=True,
                    delay=delay))
            self._inside_conjunction = False
        else:
            if type_ == ChatAction.Type.ASKING_QUESTION:
                self._sequence[-1].action_type = ChatAction.Type.ASKING_QUESTION
            self._append_to_previous(intent, text, response_template, choices=choices)
        return self

    def _create_question(self,
                         question: Union[Question, str],
                         choices: List = None,
                         parameters=None,
                         as_new_message=True
                         ):

        if choices and isinstance(question, Question):
            raise ValueError("Choices for Question objects must be defined in the questionnaire.yml and cannot be "
                             "provided as arguments.")

        default_question_params = dict(question=question)
        if parameters:
            parameters.update(default_question_params)
        else:
            parameters = default_question_params

        if isinstance(question, Question):
            surrounding = self.loader.select('question_surrounding')
            text = self.renderer.render_template(surrounding.text_template, parameters, recursive=True)
            choices = question.choices
        elif isinstance(question, str):
            text = self.renderer.load_and_render(intent=question, template_selector=self.loader, parameters=parameters)
        else:
            raise ValueError(f"Incompatible type of question: {type(question)}")

        if choices:
            choices = [self.renderer.load_and_render(x, safe=True) for x in choices]

        question_id = question.id if isinstance(question, Question) else question

        return self._create_action(question_id, text, choices=choices, type_=ChatAction.Type.ASKING_QUESTION,
                                   as_new_message=as_new_message)

    def __str__(self):
        return ' then '.join(
            f"{'send' if x.action_type == ChatAction.Type.SAYING else 'ask'} {x.render()}"
            for x in self.collect_actions()
        )
