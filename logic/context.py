from collections import deque
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Deque, Dict, List, Union

from clients.nlpclients import MessageUnderstanding
from corpus.questions import Question
from logic.chataction import ChatAction
from model import Update, User


class States(Enum):
    NONE = 0
    EXCPECTING_ANSWER = 1
    WAITING = 2


class Context:
    """
    Stores machine-understandable data about the recent conversation context
    """
    SIZE_LIMIT = 50

    def __init__(self, user: User):
        self.user = user

        # User and Bot utterances from newest to oldest
        self._utterances = deque([], maxlen=self.SIZE_LIMIT)  # type: Deque[MessageUnderstanding, ChatAction]
        self._state = States.NONE  # type: States
        self._question = None  # type: Question

    def add_incoming(self, understanding: MessageUnderstanding):
        self._utterances.appendleft(understanding)

    def add_outgoing(self, actions: List[ChatAction]):
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

    def find_incoming_utterances(
            self,
            filter_func: Callable[[MessageUnderstanding], bool],
            age_limit: Union[timedelta, datetime, int] = 10,
            only_latest: bool = True
    ) -> Union[MessageUnderstanding, List[MessageUnderstanding]]:
        return self._filter_utterances(MessageUnderstanding, filter_func, age_limit, only_latest)

    def find_outgoing_utterances(
            self,
            filter_func: Callable[[ChatAction], bool],
            age_limit: Union[timedelta, datetime, int] = 10,
            only_latest: bool = True
    ) -> Union[ChatAction, List[ChatAction]]:
        return self._filter_utterances(ChatAction, filter_func, age_limit, only_latest)

    @property
    def last_utterance(self):
        return self._utterances[-1]

    @property
    def last_incoming_utterance(self):
        try:
            return next(x for x in self._utterances if isinstance(x, MessageUnderstanding))
        except StopIteration:
            return None

    @property
    def question(self):
        return self._question

    @question.setter
    def question(self, value):
        self._question = value

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._state = value


class UserContexts:
    def __init__(self):
        self.contexts = {}  # type: Dict[User, Context]

    def add_outgoing_action(self, action: ChatAction) -> Context:
        ctx = self.get_user_context(action.peer)
        ctx.add_outgoing(action)
        return ctx

    def add_incoming_update(self, update: Update) -> Context:
        if not update.understanding:
            raise ValueError("Update has no NLP understanding attached.")
        ctx = self.get_user_context(update.user)
        ctx.add_incoming(update.understanding)
        return ctx

    def add_incoming_understanding(self, user: User, nlu: MessageUnderstanding) -> Context:
        ctx = self.get_user_context(user)
        ctx.add_incoming(nlu)
        return ctx

    def get_user_context(self, user: User):
        if user not in self.contexts.keys():
            self.contexts[user] = Context(user)
        return self.contexts[user]
