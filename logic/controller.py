# class ConversationController(object):

#     def __init__(self):
#         pass
from abc import ABCMeta, abstractmethod
from typing import Callable

from logzero import logger


class BaseHandler(metaclass=ABCMeta):
    def __init__(self, handler: Callable):
        self.handler = handler

    @abstractmethod
    def matches(self, intent, parameters): pass

    def __str__(self):
        return self.handler.__name__


class IntentHandler(BaseHandler):
    def __init__(self,
                 handler: Callable,
                 intents=None,
                 parameters=None,
                 ):
        self._intents = [intents] if isinstance(intents, str) else intents
        self._parameters = [parameters] if isinstance(parameters, str) else parameters
        super(IntentHandler, self).__init__(handler)

    def matches(self, intent, parameters):
        """
        Returns True if any intent or parameter of the arguments is matched with the ones defined in this BaseHandler.
        """
        if self._intents is not None:
            if intent not in self._intents:
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


class AffirmationHandler(BaseHandler):
    INTENTS = ['yes', 'correct', 'smalltalk.dialog.correct']

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
    INTENTS = ['no', 'wrong', 'smalltalk.dialog.wrong']

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
    def __init__(self, rules, warn_bypassed=True):
        self.warn_bypassed = warn_bypassed
        self.states = {}
        self.fallbacks = []
        self.stateless = []
        self.add_rules_dict(rules)

    def add_rules_dict(self, rules_dict):
        states = rules_dict.get('states', {})
        fallbacks = rules_dict.get('fallbacks', [])
        stateless = rules_dict.get('stateless', [])

        if any(isinstance(x, Controller) for x in stateless):
            raise ValueError("Stateless handlers cannot be Controllers.")

        for state, handlers in states.items():
            for handler in handlers:
                self.states.setdefault(state, []).append(handler)

        for handler in fallbacks:
            self.fallbacks.append(handler)

        for handler in stateless:
            self.stateless.append(handler)

    def execute(self, state, intent, parameters, *callback_args):
        for rule in self.stateless:
            # Non-breaking, execute all
            if rule.matches(intent, parameters):
                rule.handler(*callback_args)
                logger.debug(f"Stateless handler {rule} triggered.")
        for rule in self.states.get(state, []):
            # break after first occurence
            if isinstance(rule, Controller):
                next_state = rule.execute(state, intent, parameters, *callback_args)
                if next_state:
                    return next_state
            elif rule.matches(intent, parameters):
                next_state = rule.handler(*callback_args)
                if next_state:
                    logger.debug(f"{rule} triggered"
                                 f"{f' and switched to new state {next_state}' if next_state else ''}.")
                    return next_state
        for rule in self.fallbacks:
            if isinstance(rule, Controller):
                next_state = rule.execute(state, intent, parameters, *callback_args)
                if next_state:
                    return next_state
            elif rule.matches(intent, parameters):
                next_state = rule.handler(*callback_args)
                if next_state:
                    logger.debug(f"Fallback handler {rule} triggered.")
                    return next_state

        if self.warn_bypassed:
            logger.warning(f"No matching rule found in state {state} with intent "
                           f"{intent} and parameters {parameters}. Consider adding "
                           f"a fallback to the controller.")


if __name__ == '__main__':
    c = Controller()
    c._add_rule(('asking', 'claim_damage'), IntentHandler('ayy', None, 'yes'))

    print(c.get_state_handler(('asking', 'claim_damage'), None, 'yes'))
    print(c.get_state_handler(('asking', 'claim_damage'), None, 'no'))
