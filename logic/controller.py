# class ConversationController(object):
#     def __init__(self):
#         pass
from pprint import pprint
from typing import Callable, List


class IntentHandler(object):
    def __init__(self,
                 handler: Callable,
                 intents=None,
                 parameters=None,
                 ):
        self.handler = handler
        self._intents = [intents] if isinstance(intents, str) else intents
        self._parameters = [parameters] if isinstance(parameters, str) else parameters

    def matches(self, intent, parameters):
        """
        Returns True if any intent or parameter of the arguments is matched with the ones defined in this Handler.
        """
        if self._intents is not None:
            if intent not in self._intents:
                return False
        if self._parameters is not None and parameters is not None:
            for p in self._parameters:
                if p not in parameters.keys():
                    return False
        return True


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
            if handler.matches(intent, parameters):
                return handler

    def get_fallback_handler(self, intent, parameters) -> IntentHandler:
        for handler in self.fallbacks:
            if handler.matches(intent, parameters):
                return handler

    def get_stateless_handlers(self, intent, parameters) -> List[IntentHandler]:
        matching = list()
        for handler in self.stateless:
            if handler.matches(intent, parameters):
                matching.append(handler)
        return matching


if __name__ == '__main__':
    c = Controller()
    c._add_rule(('asking', 'claim_damage'), IntentHandler('ayy', None, 'yes'))

    print(c.get_state_handler(('asking', 'claim_damage'), None, 'yes'))
    print(c.get_state_handler(('asking', 'claim_damage'), None, 'no'))
