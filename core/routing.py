import re
from abc import ABCMeta, abstractmethod
from pprint import pprint
from typing import Callable

from core import MessageUnderstanding, States
from corpus import emojis
from corpus.emojis.emoji import is_emoji
from logic.intents import AFFIRMATION_INTENTS, MEDIA_INTENT, NEGATION_INTENTS


class BaseHandler(metaclass=ABCMeta):
    """
    Base class for a handler to filter and route incoming utterances to their respective callbacks.
    """

    def __init__(self, callback: Callable):
        self.callback = callback

    @abstractmethod
    def matches(self, understanding: MessageUnderstanding) -> bool: pass

    def __str__(self):
        return self.callback.__name__


class RegexHandler(BaseHandler):
    """
    Handler to filter the text of incoming utterances based on a regex `pattern`.
    """

    def __init__(self, callback: Callable, pattern, flags=0):
        self.pattern = re.compile(pattern, flags)
        super(RegexHandler, self).__init__(callback)

    def matches(self, understanding: MessageUnderstanding):
        if not understanding.text:
            return False
        return self.pattern.match(understanding.text)


class IntentHandler(BaseHandler):
    """
    Handler to filter incoming `MessageUnderstandings` based on their intents and/or parameters.
    """

    def __init__(self, callback: Callable, intents=None, parameters=None):
        """
        :param callback: Callback function
        :param intents: List of prefixes that the intent must start with
        :param parameters: List of exact parameters that must be contained in the message
        """
        if not callable(callback):
            raise ValueError("First argument `callback` must be callable.")
        self._intents = [intents] if isinstance(intents, str) else intents
        self._parameters = [parameters] if isinstance(parameters, str) else parameters
        super(IntentHandler, self).__init__(callback)

    def contains_intent(self, intent):
        return intent in self._intents

    def matches(self, understanding: MessageUnderstanding):
        """
        Returns True if intents and parameters match the rules of this handler instance.

        If a **list of intents** is defined, then **only one** of the incoming intents must
        match. The intent comparison is done via `intent.startswith(self.expected_intent)`.

        If a **list of parameters** is defined, then **all** of the corresponding incoming parameters must be non-empty.
        """
        if self._intents is not None:
            if not any(understanding.intent.startswith(x) for x in self._intents):
                return False
        if self._parameters:
            if not understanding.parameters:
                return False
            for p in self._parameters:
                if p in understanding.parameters.keys():
                    # Check if value is non-empty
                    if not understanding.parameters[p]:
                        return False
                else:
                    return False
        return True

    def __str__(self):
        return f"{self.__class__.__name__}(" \
               f"{self.callback.__name__}, " \
               f"intents={str(self._intents)[:70]}, " \
               f"parameters={self._parameters})"

    def __repr__(self):
        return f"{self._intents} / {self._parameters} --> {self.callback.__name__}"


class AffirmationHandler(BaseHandler):
    """
    Handler to conveniently filter all affirmative intents ("yes", "correct", "smalltalk.agent.right", etc.)
    """

    def __init__(self, callback):
        self.intents = AFFIRMATION_INTENTS
        super(AffirmationHandler, self).__init__(callback)

    def matches(self, understanding: MessageUnderstanding):
        if understanding.parameters:
            for k, v in understanding.parameters.items():
                if k in self.intents and v:
                    return True

        if understanding.intent in self.intents:
            return True

        return False


class NegationHandler(BaseHandler):
    """
    Handler to conveniently filter all negative intents ("no", "wrong", "smalltalk.dialog.wrong", etc.)
    """

    def __init__(self, callback):
        self.intents = NEGATION_INTENTS
        super(NegationHandler, self).__init__(callback)

    def matches(self, understanding: MessageUnderstanding):
        if understanding.parameters:
            for k, v in understanding.parameters.items():
                if k in self.intents and v:
                    return True

        if understanding.intent in self.intents:
            return True

        return False


class MediaHandler(BaseHandler):
    """
    Handler to filter incoming media entities (Videos, Images, Stickers, etc.)
    The `MessageUnderstanding` will have a special flag for an intent in that case, set by the `DialogManager`.
    """

    def __init__(self, callback):
        super(MediaHandler, self).__init__(callback)

    def matches(self, understanding: MessageUnderstanding):
        return understanding.intent == MEDIA_INTENT


class EmojiHandler(BaseHandler):
    """
    Handler to filter incoming emojis based on their sentiment score.
    """

    def __init__(self, callback, negative=False, neutral=False, positive=False, threshold=0.5):
        """
        There are three distinct categories of sentiment for a particular emoji: `negative`, `neutral` and `positive`.

        :param callback: Callback to execute on match
        :param negative: Whether to match emojis with negative sentiment
        :param neutral: Whether to match emojis with neutral sentiment
        :param positive: Whether to match emojis with positive sentiment
        :param threshold: Ratio between 0 and 1 that is applied to each category
        """
        self.negative = negative
        self.neutral = neutral
        self.positive = positive
        self.all_emotions = not any((negative, neutral, positive))
        self.threshold = threshold
        super(EmojiHandler, self).__init__(callback)

    def matches(self, understanding: MessageUnderstanding):
        # Short-circuit if all emotions (=all emojis) should be matched
        if not understanding.text:
            return False
        if self.all_emotions:
            return any(is_emoji(c) for c in understanding.text)

        total = 0
        neg = 0
        neut = 0
        pos = 0

        for x in understanding.text:
            emoji = emojis.sentiments.get(x)
            if not emoji:
                continue

            total += 1
            neg += emoji["negative"]
            neut += emoji["neutral"]
            pos += emoji["positive"]

        if total == 0:
            return False

        return any((
            self.negative and (neg / total) >= self.threshold,
            self.neutral and (neut / total) >= self.threshold,
            self.positive and (pos / total) >= self.threshold,
        ))


class Router(object):
    """
    Holds handlers that the application defines.

    - `stateless` handlers are matched independent of the current state of the dialog.
    - `states` is a mapping of a particular `state` to its appropriate handlers.
    - `fallbacks` are handlers that are matched if no matching handler could be found for the current state of the
    dialog.

    """

    def __init__(self, rules=None, warn_bypassed=True):
        self.warn_bypassed = warn_bypassed
        self.states = {}
        self.fallbacks = []
        self.stateless = []
        if rules:
            self.add_rules_dict(rules)

    def add_rules_dict(self, rules_dict):
        states = rules_dict.get('dialog_states', {})
        fallbacks = rules_dict.get('fallbacks', []) + rules_dict.get(States.FALLBACK, [])
        stateless = rules_dict.get('stateless', []) + rules_dict.get(States.STATELESS, [])

        self.fallbacks.extend(self._flatten(fallbacks))
        self.stateless.extend(self._flatten(stateless))
        for state, handlers in states.items():
            handler_list = self._flatten(handlers)
            self.states.setdefault(state, []).extend(handler_list)

    def iter_stateless_matches(self, understanding: MessageUnderstanding):
        for rule in self.stateless:
            # Non-breaking, yield all
            if rule.matches(understanding):
                yield rule

    def find_matching_state_handler(self, state, understanding: MessageUnderstanding):
        for rule in self.states.get(state, []):
            # break after first occurence
            if rule.matches(understanding):
                return rule
        return None

    def get_fallback_handler(self, understanding: MessageUnderstanding):
        for rule in self.fallbacks:
            # break after first occurence
            if rule.matches(understanding):
                return rule
        return None

    @staticmethod
    def _flatten(obj):
        for i in obj:
            if isinstance(i, (list, tuple)):
                yield from Router._flatten(i)
            else:
                yield i
