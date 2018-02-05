# class ConversationController(object):

#     def __init__(self):
#         pass
from abc import ABCMeta, abstractmethod
from typing import Callable, List
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

    def __init__(self, handler):
        super(AffirmationHandler, self).__init__(handler)

    def matches(self, intent, parameters):
        if parameters:
            for k, v in parameters.items():
                if k in ['yes', 'correct'] and v:
                    return True

        if intent in ['yes', 'correct']:
            return True

        return False


class NegationHandler(BaseHandler):

    def __init__(self, handler):
        super(NegationHandler, self).__init__(handler)

    def matches(self, intent, parameters):
        if parameters:
            for k, v in parameters.items():
                if k in ['no', 'wrong'] and v:
                    return True

        if intent in ['no', 'wrong']:
            return True

        return False


class Controller(object):
    def __init__(self, rules):
        self.states = {}
        self.fallbacks = []
        self.stateless = []
        self.add_rules_dict(rules)

    def add_rules_dict(self, rules_dict):
        states = rules_dict.get('states', {})
        fallbacks = rules_dict.get('fallbacks', [])
        always = rules_dict.get('stateless', [])

        for state, handlers in states.items():
            for handler in handlers:
                self.states.setdefault(state, []).append(handler)

        for handler in fallbacks:
            self.fallbacks.append(handler)

        for handler in always:
            self.stateless.append(handler)

    def get_state_handler(self, state, intent, parameters) -> IntentHandler:
        state_handlers = self.states.get(state, [])

        for handler in state_handlers:
            if handler.matches(intent, parameters) or isinstance(handler, Controller):
                return handler

    def get_fallback_handler(self, intent, parameters) -> IntentHandler:
        for handler in self.fallbacks:
            if handler.matches(intent, parameters) or isinstance(handler, Controller):
                return handler

    def get_stateless_handlers(self, intent, parameters) -> List[IntentHandler]:
        matching = list()
        for handler in self.stateless:
            if handler.matches(intent, parameters) or isinstance(handler, Controller):
                matching.append(handler)
        return matching

    def execute(self, state, intent, parameters, *callback_args):
        rule = self.get_state_handler(state, intent, parameters)
        fallback_rule = self.get_fallback_handler(intent, parameters)
        stateless_rules = self.get_stateless_handlers(intent, parameters)

        next_state = None
        if stateless_rules:
            for r in stateless_rules:
                if isinstance(r, Controller):
                    r.execute(state, intent, parameters, *callback_args)
                else:
                    r.handler(*callback_args)
                    logger.debug(f"Stateless handler {r} triggered.")
        if rule:
            if isinstance(rule, Controller):
                next_state = rule.execute(state, intent, parameters, *callback_args)
            else:
                next_state = rule.handler(*callback_args)
                logger.debug(f"{rule} triggered"
                             f"{f' and switched to new state {next_state}' if next_state else ''}.")
        elif fallback_rule:
            if isinstance(fallback_rule, Controller):
                next_state = fallback_rule.execute(state, intent, parameters, *callback_args)
            else:
                next_state = fallback_rule.handler(*callback_args)
                logger.debug(f"Fallback handler {fallback_rule} triggered.")
        else:
            # should not happen
            logger.warning(f"No matching rule found in state {state} with intent "
                           f"{intent} and parameters {parameters}. Consider adding "
                           f"a fallback to the controller.")
        return next_state


if __name__ == '__main__':
    c = Controller()
    c._add_rule(('asking', 'claim_damage'), IntentHandler('ayy', None, 'yes'))

    print(c.get_state_handler(('asking', 'claim_damage'), None, 'yes'))
    print(c.get_state_handler(('asking', 'claim_damage'), None, 'no'))
