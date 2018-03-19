import datetime
import random
from pprint import pprint
from typing import List

from collections import Counter
from logzero import logger as log

from const import MONTHS
from core import Context
from core.controller import Controller
from core.planningagent import IPlanningAgent
from corpus.responsetemplates import SelectiveTemplateLoader, TemplateRenderer, TemplateSelector, ResponseTemplate
from logic.sentencecomposer import SentenceComposer
from model import UserAnswers


class PlanningAgent(IPlanningAgent):
    def __init__(self, controller: Controller):
        self.controller = controller

    def build_next_actions(self, context) -> SentenceComposer:
        user_utterance = context.last_user_utterance

        def chance(value: float) -> bool:
            return random.random() < value

        shared_parameters = dict(
            user=context.user,
            get_answer=lambda identifier: UserAnswers.get_answer(context.user, identifier),
            questionnaire_completion=context.questionnaire_completion_ratio,
            user_recent=context.has_user_intent,
            bot_recent=context.has_outgoing_intent,
            question=context.current_question,
            questionnaire=context.current_questionnaire,
            overall_completion=context.overall_completion_ratio,
            num_actions=lambda intent: len(context.filter_outgoing_utterances(
                lambda ca: intent in ca.intents, 12)),
            get=lambda key: context.get_value(key, None),
            formal=context.user.formal_address,
            informal=not context.user.formal_address,
            chance=chance,
            month=lambda n: MONTHS.get(n),
            is_this_year=lambda y: y == datetime.datetime.now().year
        )

        lru_selector = LeastRecentlyUsedSelector(context)
        composer = SentenceComposer(
            context.user,
            SelectiveTemplateLoader(shared_parameters, template_selector=lru_selector),
            TemplateRenderer(shared_parameters)
        )

        log.debug(f'Incoming message: {user_utterance.intent} / {user_utterance.parameters} '
                  f'|| Current state: {context.state}')

        # Rule-based planning algorithm
        next_state = self.controller.execute(context.state,
                                             context.last_user_utterance.intent,
                                             context.last_user_utterance.parameters,
                                             composer, context)
        if next_state:
            context.state = next_state

        text = ', then '.join(f'"{x.render()}"' for x in composer.collect_actions())
        log.debug(f'Sending {text}')
        return composer


class LeastRecentlyUsedSelector(TemplateSelector):
    def __init__(self, context: Context):
        self.context = context

    def select_template(self, candidates: List[ResponseTemplate]):
        used_templates = self.context.setdefault('used_templates', Counter())

        if len(candidates) == 1:
            selection = candidates[0]
        else:
            best_candidate = (100, None)
            for c in candidates:
                usages = used_templates.get(c.original_text, 0)
                if usages == 0:
                    best_candidate = (0, c)
                    break
                if usages < best_candidate[0]:
                    best_candidate = (usages, c)
            selection = best_candidate[1]

        used_templates.update([selection.original_text])
        self.context.set_value('used_templates', used_templates)
        return selection
