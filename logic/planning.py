from abc import ABCMeta, abstractmethod

from corpus.sentencecomposer import SentenceComposer
from logzero import logger

from corpus.responsetemplates import SelectiveTemplateLoader
from logic.controller import Controller


class IPlanningAgent(metaclass=ABCMeta):
    @abstractmethod
    def build_next_actions(self, context) -> SentenceComposer: pass


class PlanningAgent(IPlanningAgent):
    def __init__(self, controller: Controller):
        self.controller = controller

    def build_next_actions(self, context) -> SentenceComposer:
        user_utterance = context.last_user_utterance

        load_context = dict(
            user=context.user,
            questionnaire_completion=context.questionnaire_completion_ratio,
            user_recent=context.has_user_intent,
            bot_recent=context.has_outgoing_intent,
            question=context.current_question,
            questionnaire=context.current_questionnaire,
            overall_completion=context.overall_completion_ratio,
        )
        # TODO: Inject load context, not the merged dict
        selection_context = dict(
            num_actions=lambda intent: len(context.filter_outgoing_utterances(
                lambda ca: ca.intent == intent, 12))
        )
        selection_context.update(load_context)

        composer = SentenceComposer(
            context.user,
            SelectiveTemplateLoader(selection_context),
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
