from abc import ABCMeta, abstractmethod

from logzero import logger

from corpus.responsecomposer import ResponseComposer
from corpus.responsetemplates import SelectiveTemplateLoader
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
            user=context.user,
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

        logger.debug(f'Incoming message: {user_utterance.intent} / {user_utterance.parameters}')

        # Rule-based planning algorithm
        next_state = self.controller.execute(context.state,
                                             context.last_user_utterance.intent,
                                             context.last_user_utterance.parameters,
                                             composer, context)
        if next_state:
            context.state = next_state

        return composer
