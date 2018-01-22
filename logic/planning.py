from abc import ABCMeta, abstractmethod

from corpus.responsecomposer import ResponseComposer
from corpus.templates import SelectiveTemplateLoader
from logic.controller import Controller


class IPlanningAgent(metaclass=ABCMeta):
    @abstractmethod
    def build_next_actions(self, context) -> ResponseComposer: pass


class PlanningAgent(IPlanningAgent):
    def __init__(self, controller: Controller):
        self.controller = controller

    def build_next_actions(self, context) -> ResponseComposer:
        user_utterance = context.last_user_utterance

        load_and_selection_context = dict(
            questionnaire_completion=context.questionnaire_completion_ratio,
            user_recent=context.has_user_intent,
            bot_recent=context.has_outgoing_intent,
            question=context.current_question,
            questionnaire=context.current_questionnaire,
            overall_completion=context.overall_completion_ratio
        )
        composer = ResponseComposer(
            context.user,
            SelectiveTemplateLoader(load_and_selection_context),
        )

        print(f"New incoming message '{user_utterance.text}' with INTENT['{user_utterance.intent}'], "
              f"PARAMETERS['{user_utterance.parameters}']")

        # Rule-based planning algorithm
        rule = self.controller.get_state_handler(
            context.state,
            user_utterance.intent,
            user_utterance.parameters,
        )
        fallback_rule = self.controller.get_fallback_handler(user_utterance.intent, user_utterance.parameters)
        stateless_rules = self.controller.get_stateless_handlers(user_utterance.intent, user_utterance.parameters)

        if stateless_rules:
            for r in stateless_rules:
                r.handler(composer, context)
        if rule:
            new_state = rule.handler(composer, context)
        elif fallback_rule:
            new_state = fallback_rule.handler(composer, context)
        else:
            # should not happen
            print(f"No matching rule found in state {context.state} with intent "
                  f"{user_utterance.intent} and parameters {user_utterance.parameters}. Consider adding "
                  f"a fallback to the controller.")
            composer.say('sorry').concat('did not understand')
            return composer
        if new_state is not None:
            # Keep the state if method returned None
            context.state = new_state
            print(f"New state: {new_state}")

        print(f"Overall completion ratio: {context.overall_completion_ratio}")
        return composer
