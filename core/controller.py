# class ConversationController(object):

#     def __init__(self):
#         pass
from abc import ABCMeta, abstractmethod
from typing import Callable

from logzero import logger

from core import States


class BaseHandler(metaclass=ABCMeta):
    def __init__(self, handler: Callable):
        self.handler = handler

    @abstractmethod
    def matches(self, intent, parameters): pass

    def __str__(self):
        return self.handler.__name__


class IntentHandler(BaseHandler):
    """
    Handler definition that triggers on specific intents and/or parameters of incoming messages.
    """

    def __init__(self, handler: Callable, intents=None, parameters=None):
        """
        :param handler: Callback function
        :param intents: List of prefixes that the intent must start with
        :param parameters: List of exact parameters that must be contained in the message
        """
        if not callable(handler):
            raise ValueError("First argument `handler` must be callable.")
        self._intents = [intents] if isinstance(intents, str) else intents
        self._parameters = [parameters] if isinstance(parameters, str) else parameters
        super(IntentHandler, self).__init__(handler)

    def contains_intent(self, intent):
        return intent in self._intents

    def matches(self, intent, parameters):
        """
        Returns True if any intent or parameter of the arguments is matched with the ones defined in this BaseHandler.
        """
        if self._intents is not None:
            if not any(intent.startswith(x) for x in self._intents):
                return False
        if self._parameters:
            if not parameters:
                return False
            for p in self._parameters:
                if p in parameters.keys():
                    # Check if value is non-empty
                    if not parameters[p]:
                        return False
                else:
                    return False
        return True

    def __str__(self):
        return f"{self._intents} / {self._parameters} --> {self.handler.__name__}"

    def __repr__(self):
        return f"{self.__class__.__name__}(" \
               f"{self.handler.__name__}, " \
               f"intents={self._intents}, " \
               f"parameters={self._parameters})"


class AffirmationHandler(BaseHandler):
    INTENTS = ['yes', 'correct', 'smalltalk.dialog.correct', 'smalltalk.agent.right']

    def __init__(self, handler):
        super(AffirmationHandler, self).__init__(handler)

    def matches(self, intent, parameters):
        if parameters:
            for k, v in parameters.items():
                if k in self.INTENTS and v:
                    return True

        if intent in self.INTENTS:
            return True

        return False


class NegationHandler(BaseHandler):
    INTENTS = ['no', 'wrong', 'smalltalk.dialog.wrong', 'skip', 'smalltalk.agent.wrong']

    def __init__(self, handler):
        super(NegationHandler, self).__init__(handler)

    def matches(self, intent, parameters):
        if parameters:
            for k, v in parameters.items():
                if k in self.INTENTS and v:
                    return True

        if intent in self.INTENTS:
            return True

        return False


class Controller(object):
    # TODO: remove nesting of controllers
    def __init__(self, rules=None, warn_bypassed=True):
        self.warn_bypassed = warn_bypassed
        self.states = {}
        self.fallbacks = []
        self.stateless = []
        if rules:
            self.add_rules_dict(rules)

    def add_rules_dict(self, rules_dict):
        states = rules_dict.get('states', {})
        fallbacks = rules_dict.get('fallbacks', []) + rules_dict.get(States.FALLBACK, [])
        stateless = rules_dict.get('stateless', []) + rules_dict.get(States.STATELESS, [])

        if any(isinstance(x, Controller) for x in stateless):
            raise ValueError("Stateless handlers cannot be Controllers.")

        self.fallbacks.extend(self._flatten(fallbacks))
        self.stateless.extend(self._flatten(stateless))
        for state, handlers in states.items():
            handler_list = self._flatten(handlers)
            self.states.setdefault(state, []).extend(handler_list)

    # def on_intent(self, state, intents=None, parameters=None):
    #     def decorator(func):
    #         handler = IntentHandler(func, intents, parameters)
    #         if state == 'fallback' or state == States.FALLBACK:
    #             self.fallbacks.append(handler)
    #         elif state == 'stateless' or state == States.STATELESS:
    #             self.stateless.append(handler)
    #         else:
    #             self.states.setdefault(state, []).append(handler)
    #
    #         def wrapped(*args, **kwargs):
    #             return func(*args, **kwargs)
    #
    #         return wrapped
    #
    #     return decorator

    def execute(self, state, intent, parameters, *callback_args):
        for rule in self.stateless:
            # Non-breaking, execute all
            if rule.matches(intent, parameters):
                rule.handler(*callback_args)
                logger.debug(f"Stateless handler {rule} triggered.")
        for rule in self.states.get(state, []):
            # break after first occurence
            if rule.matches(intent, parameters):
                next_state = rule.handler(*callback_args)
                logger.debug(f"{rule} triggered"
                             f"{f' and switched to new state {next_state}' if next_state else ''}.")
                return next_state
        for rule in self.fallbacks:
            # break after first occurence
            if rule.matches(intent, parameters):
                next_state = rule.handler(*callback_args)
                logger.debug(f"Fallback handler {rule} triggered.")
                return next_state

        if self.warn_bypassed:
            logger.warning(f"No matching rule found in state {state} with intent "
                           f"{intent} and parameters {parameters}. Consider adding "
                           f"a fallback to the controller.")

    @staticmethod
    def _flatten(obj):
        for i in obj:
            if isinstance(i, (list, tuple)):
                yield from Controller._flatten(i)
            else:
                yield i


if __name__ == '__main__':
    c = Controller()
    c._add_rule(('asking', 'claim_damage'), IntentHandler('ayy', None, 'yes'))

    print(c.get_state_handler(('asking', 'claim_damage'), None, 'yes'))
    print(c.get_state_handler(('asking', 'claim_damage'), None, 'no'))
