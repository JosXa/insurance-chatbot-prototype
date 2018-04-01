import datetime
import random
from collections import Counter
from typing import List, Union

from logzero import logger as log

from const import MONTHS
from core import Context
from core.planningagent import IPlanningAgent
from core.routing import Router
from corpus.responsetemplates import ResponseTemplate, SelectiveTemplateLoader, TemplateRenderer, TemplateSelector
from logic.rules.claimhandlers import excuse_did_not_understand, no_rule_found
from logic.sentencecomposer import SentenceComposer
from model import UserAnswers


class PlanningAgent(IPlanningAgent):
    def __init__(self, router: Router):
        self.router = router

    def build_next_actions(self, context: Context) -> Union[SentenceComposer, None]:
        u = context.last_user_utterance

        def chance(value: float) -> bool:
            return random.random() < value

        # Declare parameters to be used in jinja2-templates
        shared_parameters = dict(
            user=context.user,
            get_answer=lambda identifier: UserAnswers.get_answer(context.user, identifier),
            has_answered=lambda identifier: UserAnswers.has_answered(context.user, identifier),
            questionnaire_completion=context.questionnaire_completion_ratio,
            user_recent=context.has_incoming_intent,
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

        text = f'"{u.text[:40]}"' if u.text else ''
        log.info(f'Incoming message: {text}, {u}')
        log.debug(f'Current dialog states: {context.dialog_states}')

        # Execute every matching stateless handler first
        for handler in self.router.iter_stateless_matches(u):
            if handler.callback(composer, context):
                log.debug(f"Stateless handler triggered: {handler}")

        next_state = None
        # Dialog states are a priority queue
        for state in context.dialog_states.iter_states():
            # Find exactly one handler in any of the prioritized states
            handler = self.router.find_matching_state_handler(state, u)

            if handler is None:
                continue

            next_state = handler.callback(composer, context)
            log.info(f"State handler triggered: {handler}")
            handler_found = True
            break
        else:
            # If no handler was found in any of the states, try the fallbacks
            handler = self.router.get_fallback_handler(u)

            if handler is not None:
                next_state = handler.callback(composer, context)
                log.info(f"Fallback handler triggered: {handler}")
                handler_found = True
            else:
                log.warning(f"No matching rule found in dialog_states "
                            f"{list(context.dialog_states.iter_states())} with intent "
                            f"{u.intent} and parameters {u.parameters}.")
                handler_found = False

        if not handler_found:
            if u.intent == 'fallback':
                excuse_did_not_understand(composer, context)
                log.debug(f'Incoming message was not understood: "{u.text}"')
                log.debug("Not updating state lifetimes.")
                return composer
            else:
                next_state = no_rule_found(composer, context)

        if isinstance(next_state, SentenceComposer):
            # Lambdas return the senctence composer, which we don't need (call by reference)
            next_state = None

        if next_state is not None:
            # Handlers return a tuple with the next state, with an integer determining the lifetime of this state as
            # the last tuple value.
            # E.g. `("asking", "do_something", 3)`  <-- lifetime of 3 incoming utterances
            context.dialog_states.put(next_state)
            return composer

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
