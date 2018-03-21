# class ConversationController(object):

#     def __init__(self):
#         pass
import re
from abc import ABCMeta, abstractmethod
from typing import Callable

from core import MessageUnderstanding, States
from corpus import emojis
from corpus.emojis.emoji import is_emoji


class BaseHandler(metaclass=ABCMeta):
    def __init__(self, callback: Callable):
        self.callback = callback

    @abstractmethod
    def matches(self, understanding: MessageUnderstanding): pass

    def __str__(self):
        return self.callback.__name__


class RegexHandler(BaseHandler):
    def __init__(self, callback: Callable, pattern, flags=0):
        self.pattern = re.compile(pattern, flags)
        super(RegexHandler, self).__init__(callback)

    def matches(self, understanding: MessageUnderstanding):
        return self.pattern.match(understanding.text)


class IntentHandler(BaseHandler):
    """
    Handler definition that triggers on specific intents and/or parameters of incoming messages.
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
        Returns True if any intent or parameter of the arguments is matched with the ones defined in this BaseHandler.
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
               f"intents={str(self._intents)[:40]}, " \
               f"parameters={self._parameters})"

    def __repr__(self):
        return f"{self._intents} / {self._parameters} --> {self.callback.__name__}"


class AffirmationHandler(BaseHandler):
    INTENTS = ['yes', 'correct', 'smalltalk.dialog.correct',
               'smalltalk.agent.right']

    def __init__(self, callback):
        super(AffirmationHandler, self).__init__(callback)

    def matches(self, understanding: MessageUnderstanding):
        if understanding.parameters:
            for k, v in understanding.parameters.items():
                if k in self.INTENTS and v:
                    return True

        if understanding.intent in self.INTENTS:
            return True

        return False


class NegationHandler(BaseHandler):
    INTENTS = ['no', 'wrong', 'smalltalk.dialog.wrong', 'skip',
               'smalltalk.agent.wrong', 'smalltalk.dialog.wrong']

    def __init__(self, callback):
        super(NegationHandler, self).__init__(callback)

    def matches(self, understanding: MessageUnderstanding):
        if understanding.parameters:
            for k, v in understanding.parameters.items():
                if k in self.INTENTS and v:
                    return True

        if understanding.intent in self.INTENTS:
            return True

        return False


class MediaHandler(BaseHandler):

    def __init__(self, callback):
        super(MediaHandler, self).__init__(callback)

    def matches(self, understanding: MessageUnderstanding):
        return understanding.intent == 'media'


class EmojiHandler(BaseHandler):

    def __init__(self, callback, negative=False, neutral=False, positive=False, threshold=0.5):
        self.negative = negative
        self.neutral = neutral
        self.positive = positive
        self.all_emotions = not any((negative, neutral, positive))
        self.threshold = threshold
        super(EmojiHandler, self).__init__(callback)

    def matches(self, understanding: MessageUnderstanding):
        # Short-circuit if all emotions (=all emojis) should be matched
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

        print("neg", (neg / total))
        print("neut", (neut / total))
        print("pos", (pos / total))

        return any((
            self.negative and (neg / total) >= self.threshold,
            self.neutral and (neut / total) >= self.threshold,
            self.positive and (pos / total) >= self.threshold,
        ))


class Router(object):
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

        if any(isinstance(x, Router) for x in stateless):
            raise ValueError("Stateless handlers cannot be Controllers.")

        self.fallbacks.extend(self._flatten(fallbacks))
        self.stateless.extend(self._flatten(stateless))
        for state, handlers in states.items():
            handler_list = self._flatten(handlers)
            self.states.setdefault(state, []).extend(handler_list)

    def iter_matches_stateless(self, understanding: MessageUnderstanding):
        for rule in self.stateless:
            # Non-breaking, execute all
            if rule.matches(understanding):
                yield rule

    def get_state_handler(self, state, understanding: MessageUnderstanding):
        for rule in self.states.get(state, []):
            # break after first occurence
            if rule.matches(understanding):
                return rule
        return None

    def get_fallback_handler(self, understanding: MessageUnderstanding):
        for rule in self.fallbacks:
            # break after first occurence
            if rule.matches(understanding):
                # logger.debug(f"Fallback handler {rule} triggered.")
                return rule
        return None

    @staticmethod
    def _flatten(obj):
        for i in obj:
            if isinstance(i, (list, tuple)):
                yield from Router._flatten(i)
            else:
                yield i
