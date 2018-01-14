from abc import ABCMeta, abstractmethod
from typing import Tuple

from corpus import all_questionnaires
from corpus.questions import Questionnaire, Question
from corpus.responsetemplates import TemplateSelector, TemplateRenderer
from logic.chataction import ChatActionsBuilder
from logic.context import Context
from model.useranswers import UserAnswers


class IPlanningAgent(metaclass=ABCMeta):
    @abstractmethod
    def build_next_actions(self) -> ChatActionsBuilder: pass


class PlanningAgent(IPlanningAgent):
    def __init__(self, context: Context):
        self.context = context
        self.user = self.context.user
        self.templates = TemplateRenderer(user=self.user)
        self.answered_ids = UserAnswers.get_answered_question_ids(self.user)

    def _get_next_question(self) -> Tuple[Questionnaire, float, Question]:
        try:
            qn = next(q for q in all_questionnaires if q.next_question(self.answered_ids))
            completion = qn.completion_ratio(self.answered_ids)
            return qn, completion, qn.next_question(self.answered_ids)
        except StopIteration:
            return None

    def _me_said_recently(self, intent):
        result = self.context.find_outgoing_utterances(
            lambda ca: intent in ca.intents,
            only_latest=True
        )
        return bool(result)

    def _recently_spoke_about(self, intent):
        pass  # TODO

    def build_next_actions(self) -> ChatActionsBuilder:
        user_utterance = self.context.last_incoming_utterance
        current_questionnaire, qn_completion_ratio, next_question = self._get_next_question()

        builder = ChatActionsBuilder(
            self.context.user,
            TemplateSelector(qn_completion_ratio),
        )

        # Static responses
        if user_utterance.intent == 'hello':
            builder.say("hello")
            if not self._me_said_recently("what i can do"):
                builder.say("what i can do")

        if current_questionnaire.is_first_question(next_question) and len(self.answered_ids) > 0:
            # started a new questionnaire
            builder.say("well done").say("questionnaire finished").then_say(current_questionnaire.title)

        return builder
