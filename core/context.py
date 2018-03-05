from collections import deque
from datetime import datetime, timedelta
from enum import Enum
from pprint import pprint
from typing import Callable, Deque, Dict, List, Union

from logzero import logger

import settings
from core.chataction import ChatAction
from core.understanding import MessageUnderstanding
from corpus import all_questionnaires
from corpus.questions import Question, Questionnaire
from corpus.responsetemplates import format_intent
from model import Update, User, UserAnswers


class States(Enum):
    # Special
    INITIAL = 0
    FALLBACK = 1
    STATELESS = 2

    # Normal
    ASKING_QUESTION = 4


class Context:
    """
    Stores machine-understandable data about the recent conversation context
    """
    SIZE_LIMIT = 50

    def __init__(self, user: User):
        self.user = user

        # User and Bot utterances from newest to oldest
        self._utterances = deque([], maxlen=self.SIZE_LIMIT)  # type: Deque[MessageUnderstanding, ChatAction]
        self._state = States.INITIAL  # type: States
        self._state_lifetime = None
        self._value_store = dict()

        self._current_question = None  # type: Question
        self._current_questionnaire = None  # type: Questionnaire
        self._answered_question_ids = set()
        self._all_done = False
        self._update_question_context()

    def set_value(self, key, value):
        # TODO: persist to database
        self._value_store[key] = value
        return value

    def setdefault(self, key, default=None):
        return self._value_store.setdefault(key, default)

    def get_value(self, key, default=None):
        return self._value_store.get(key, default)

    def add_user_utterance(self, understanding: MessageUnderstanding):
        self._utterances.appendleft(understanding)
        if self._state_lifetime:
            logger.debug(f"Decrementing lifetime to {self._state_lifetime - 1}")
            self._state_lifetime -= 1

    def add_actions(self, actions: List[ChatAction]):
        for action in actions:
            self._utterances.appendleft(action)

    def _filter_utterances(self, utterance_type, filter_func, age_limit, only_latest):
        if isinstance(age_limit, timedelta):
            age_limit = datetime.now() - age_limit

        age = -1
        results = list()
        for utt in self._utterances:  # newest to oldest
            if not isinstance(utt, utterance_type):
                continue

            # skip ChatActions
            age += 1

            if isinstance(age_limit, datetime):
                if utt.date < age_limit:
                    continue
            elif isinstance(age_limit, int):
                if age > age_limit:
                    break
            if filter_func(utt):
                results.append(utt)
                if only_latest:
                    return utt

        return results

    def has_user_intent(self,
                        intent: str,
                        age_limit: Union[timedelta, datetime, int] = settings.CONTEXT_LOOKUP_RECENCY,
                        ) -> bool:
        intent = format_intent(intent)
        return bool(self.filter_user_utterances(
            lambda understanding: understanding.intent == intent,
            age_limit,
            only_latest=True
        ))

    def has_outgoing_intent(self,
                            intent: str,
                            age_limit: Union[timedelta, datetime, int] = settings.CONTEXT_LOOKUP_RECENCY,
                            ) -> bool:
        intent = format_intent(intent)
        return bool(self.filter_outgoing_utterances(
            lambda action: intent in action.intents,
            age_limit,
            only_latest=True
        ))

    def filter_user_utterances(
            self,
            filter_func: Callable[[MessageUnderstanding], bool],
            age_limit: Union[timedelta, datetime, int] = settings.CONTEXT_LOOKUP_RECENCY,
            only_latest: bool = False
    ) -> Union[MessageUnderstanding, List[MessageUnderstanding]]:
        pprint(self._utterances)
        return self._filter_utterances(MessageUnderstanding, filter_func, age_limit, only_latest)

    def filter_outgoing_utterances(
            self,
            filter_func: Callable[[ChatAction], bool],
            age_limit: Union[timedelta, datetime, int] = settings.CONTEXT_LOOKUP_RECENCY,
            only_latest: bool = False
    ) -> Union[ChatAction, List[ChatAction]]:
        return self._filter_utterances(ChatAction, filter_func, age_limit, only_latest)

    def add_answer_to_question(self, question, answer):
        UserAnswers.insert(user=self.user,
                           question_id=question.id if isinstance(question, Question) else question,
                           answer=answer
                           ).execute()
        self._answered_question_ids.add(question.id if isinstance(question, Question) else question)
        self._update_question_context()

    def _update_question_context(self) -> None:
        try:
            self.current_questionnaire = next(q for q
                                              in all_questionnaires
                                              if q.next_question(self._answered_question_ids))
            self._current_question = self.current_questionnaire.next_question(self._answered_question_ids)
            self._all_done = False
        except StopIteration:
            print("ALL DONE!!!")
            self._all_done = True

    @property
    def has_answered_questions(self):
        return len(self._answered_question_ids) > 0

    @property
    def last_utterance(self):
        return self._utterances[-1]

    @property
    def last_user_utterance(self):
        try:
            return next(x for x in self._utterances if isinstance(x, MessageUnderstanding))
        except StopIteration:
            return None

    @property
    def current_question(self):
        return self._current_question

    @property
    def questionnaire_completion_ratio(self):
        return self.current_questionnaire.completion_ratio(self._answered_question_ids)

    @property
    def overall_completion_ratio(self):
        return (all_questionnaires.index(self.current_questionnaire) / len(all_questionnaires)) + (
                self.questionnaire_completion_ratio / len(all_questionnaires))

    @property
    def state(self):
        if self._state_lifetime and self._state_lifetime < 0:
            return None
        return self._state

    @state.setter
    def state(self, value):
        if isinstance(value, tuple):
            try:
                # Treat last state value of tuple as new lifetime of the state
                lifetime = int(value[-1])
                new_state = value[:-1]
                self._state = new_state
                self._state_lifetime = lifetime
                return
            except:
                pass
        self._state = value
        self._state_lifetime = None


class ContextManager:
    def __init__(self):
        self.contexts = {}  # type: Dict[User, Context]

    def add_outgoing_action(self, action: ChatAction) -> Context:
        ctx = self.get_user_context(action.peer)
        ctx.add_actions(action)
        return ctx

    def add_incoming_update(self, update: Update) -> Context:
        if not update.understanding:
            raise ValueError("Update has no NLP understanding attached.")
        ctx = self.get_user_context(update.user)
        ctx.add_user_utterance(update.understanding)
        return ctx

    def add_incoming_understanding(self, user: User, nlu: MessageUnderstanding) -> Context:
        ctx = self.get_user_context(user)
        ctx.add_user_utterance(nlu)
        return ctx

    def get_user_context(self, user: User):
        if user not in self.contexts.keys():
            self.contexts[user] = Context(user)
        return self.contexts[user]
