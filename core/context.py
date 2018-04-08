import collections
import sched
import threading
import time
from collections import deque
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Deque, Dict, List, Union

from redis import StrictRedis
from redis_collections import SyncableDeque, SyncableDict

import settings
from core.chataction import ChatAction
from core.dialogstates import DialogStates
from core.understanding import MessageUnderstanding
from corpus.questions import Question, Questionnaire, all_questionnaires
from corpus.responsetemplates import format_intent
from model import Update, User, UserAnswers


class States(Enum):
    # Special
    SMALLTALK = 0
    FALLBACK = 1
    STATELESS = 2

    # Normal
    ASKING_QUESTION = 4


class Context(collections.MutableMapping):
    """
    Stores machine-understandable data about the recent conversation context.

    This includes the current state of the dialog, incoming `MessageUnderstandings` and outgoing `ChatActions`,
    the questions a user has answered so far (`_answered_question_ids`), as well as a way to calculate the next
    question applicable for a user (done automatically when new utterances are added).

    Acts like a dictionary with methods `_set_value` and `_get_value` to provide a persistent, random access data
    storage for a particular user.
    """

    # Maximum number of utterances a single context keeps stored.
    SIZE_LIMIT = 50

    def __init__(self, user: User, initial_state, redis=None):
        self.user = user

        self._redis = redis
        self._initial_state = initial_state
        self._init_collections()

        # Utterances are synced with the redis database every couple of seconds, as opposed to immediately.
        self._sync_timeout = 5  # seconds
        self._scheduler = sched.scheduler(time.time, time.sleep)
        self.__sync_utt_job = None  # type: sched.Event
        self.__utt_sync_lock = threading.Lock()

        self.__name__ = "Context"

    def _init_collections(self):
        uid = self.user.id
        self.dialog_states = DialogStates(
            self._initial_state,
            redis=self._redis,
            key=f'{uid}:ds')

        # User and Bot utterances from newest to oldest
        if self._redis:
            self._utterances = SyncableDeque(
                maxlen=self.SIZE_LIMIT,
                redis=self._redis,
                key=f'{uid}:utterances')  # type: Deque[Union[MessageUnderstanding, ChatAction]]
            self._value_store = SyncableDict(  # type: Dict
                redis=self._redis,
                writeback=True,
                key=f'{uid}:kv_store')
            self._utterances.sync()
            self._value_store.sync()
        else:
            self._utterances = deque()  # type: Deque[Union[MessageUnderstanding, ChatAction]]
            self._value_store = dict()

        self._answered_question_ids = UserAnswers.get_answered_question_ids(self.user)

        self._current_question = None  # type: Question
        self._current_questionnaire = None  # type: Questionnaire

        self._all_done = False  # type: bool
        self._update_question_context()

        # cached property
        self.__last_user_utterance = None  # type: MessageUnderstanding

    def _sched_sync_utterance(self):
        if not isinstance(self._utterances, SyncableDeque):
            return
        try:
            self._scheduler.cancel(self.__sync_utt_job)
        except ValueError:
            pass
        self.__sync_utt_job = self._scheduler.enter(self._sync_timeout, 1, self._sync_utterances)
        threading.Thread(target=self._scheduler.run).start()

    def _sync_utterances(self):
        with self.__utt_sync_lock:
            self._utterances.sync()

    def add_user_utterance(self, understanding: MessageUnderstanding):
        with self.__utt_sync_lock:
            self._utterances.appendleft(understanding)
        self.__last_user_utterance = understanding
        self._sched_sync_utterance()

    def add_actions(self, actions: List[ChatAction]):
        for action in actions:
            with self.__utt_sync_lock:
                self._utterances.appendleft(action)
        self._sched_sync_utterance()

    @property
    def claim_finished(self):
        return self._all_done

    def _filter_utterances(self, utterance_type, filter_func, age_limit, only_latest):
        """
        Filters all contained utterances by a callable `filter_func` and an `age_limit`.
        :param utterance_type: Either `MessageUnderstanding` or `ChatAction`
        :param filter_func: A function to filter the valid utterances
        :param age_limit: A timedelta or number in seconds
        :param only_latest: Return the most recent utterance only
        :return:
        """
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

    def has_incoming_intent(self,
                            intent: str,
                            age_limit: Union[timedelta, datetime, int] = settings.CONTEXT_LOOKUP_RECENCY,
                            ) -> bool:
        """
        Returns True if there has been an incoming `MessageUnderstanding` with the specified `intent` not older than
        `age_limit`.
        """
        intent = format_intent(intent)
        return bool(self.filter_incoming_utterances(
            lambda understanding: understanding.intent == intent,
            age_limit,
            only_latest=True
        ))

    def has_outgoing_intent(self,
                            intent: str,
                            age_limit: Union[timedelta, datetime, int] = settings.CONTEXT_LOOKUP_RECENCY,
                            ) -> bool:
        """
        Returns True if there has been an outgoing `ChatAction` with the specified `intent` not older than
        `age_limit`.
        """
        intent = format_intent(intent)
        return bool(self.filter_outgoing_utterances(
            lambda action: intent in action.intents,
            age_limit,
            only_latest=True
        ))

    def filter_incoming_utterances(
            self,
            filter_func: Callable[[MessageUnderstanding], bool],
            age_limit: Union[timedelta, datetime, int] = settings.CONTEXT_LOOKUP_RECENCY,
            only_latest: bool = False
    ) -> Union[MessageUnderstanding, List[MessageUnderstanding]]:
        """
        Filters all incoming utterances by a callable `filter_func` not older than `age_limit`.
        :param filter_func: A function to filter the valid utterances
        :param age_limit: A timedelta or number in seconds
        :param only_latest: Whether to return only the most recent utterance
        :return: An object or a list of type `MessageUnderstandings`
        """
        return self._filter_utterances(MessageUnderstanding, filter_func, age_limit, only_latest)

    def filter_outgoing_utterances(
            self,
            filter_func: Callable[[ChatAction], bool],
            age_limit: Union[timedelta, datetime, int] = settings.CONTEXT_LOOKUP_RECENCY,
            only_latest: bool = False
    ) -> Union[ChatAction, List[ChatAction]]:
        """
        Filters all outgoing chat actions by a callable `filter_func` not older than `age_limit`.
        :param filter_func: A function to filter the valid utterances
        :param age_limit: A timedelta or number in seconds
        :param only_latest: Whether to return only the most recent utterance
        :return: An object or a list of type `ChatAction`
        """
        return self._filter_utterances(ChatAction, filter_func, age_limit, only_latest)

    def add_answer_to_question(self, question: Union[Question, str], answer: str):
        """
        Creates a database entry for the answer given by the user to which this context belongs.
        """
        UserAnswers.add_answer(
            user=self.user,
            question_id=question.id if isinstance(question, Question) else question,
            answer=answer,
        )
        self._answered_question_ids.add(question.id if isinstance(question, Question) else question)
        self._update_question_context()

    def _update_question_context(self) -> None:
        """
        Calculates the best next question and questionnaire to ask
        depending on the `self._answered_question_ids`.
        """
        try:
            self._current_questionnaire = next(
                q for q
                in all_questionnaires
                if q.next_question(self._answered_question_ids))
            self._current_question = self._current_questionnaire.next_question(self._answered_question_ids)
            self._all_done = False
        except StopIteration:
            self._all_done = True

    @property
    def has_answered_questions(self):
        return len(self._answered_question_ids) > 0

    @property
    def last_user_utterance(self):
        return self.__last_user_utterance

    @property
    def current_question(self):
        return self._current_question

    @property
    def current_questionnaire(self):
        return self._current_questionnaire

    @property
    def questionnaire_completion_ratio(self):
        """ Returns a ratio of how many questions in the current questionnaire have been answered. """
        return self._current_questionnaire.completion_ratio(self._answered_question_ids)

    @property
    def overall_completion_ratio(self):
        """ Returns a ratio of how many questions have been answered divided by the total number of questions. """
        return (all_questionnaires.index(self._current_questionnaire) / len(all_questionnaires)) + (
                self.questionnaire_completion_ratio / len(all_questionnaires))

    def reset_all(self):
        self._init_collections()

    def __setitem__(self, key, value):
        self._value_store[key] = value
        if isinstance(self._value_store, SyncableDict):
            self._value_store.sync()
        return value

    def __delitem__(self, key):
        del self._value_store[key]

    def __getitem__(self, key):
        return self._value_store[key]

    def __len__(self):
        return len(self._value_store)

    def __iter__(self):
        return iter(self._value_store)


class ContextManager:
    """
    Holds and creates the contexts of individual users
    """

    def __init__(self, initial_state, redis: StrictRedis = None):
        self.contexts = {}  # type: Dict[int, Context]
        self.initial_state = initial_state
        self.redis = redis

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
        ctx = self.get_user_context(user.id)
        ctx.add_user_utterance(nlu)
        return ctx

    def get_user_context(self, user: User):
        try:
            return self.contexts[user.id]
        except KeyError:
            self.contexts[user.id] = Context(user, self.initial_state, redis=self.redis)
            return self.contexts[user.id]
