import datetime
import random
from collections import Counter
from typing import List, Union

from logzero import logger as log

from const import MONTHS
from core import Context
from core.dialogmanager import StopPropagation
from core.planningagent import IPlanningAgent
from core.routing import Router
from corpus.responsetemplates import ResponseTemplate, SelectiveTemplateLoader, TemplateRenderer, TemplateSelector
from logic.responsecomposer import ResponseComposer
from logic.rules.claimhandlers import excuse_did_not_understand, no_rule_found
from model import UserAnswers


class PlanningAgent(IPlanningAgent):
    """
    Concrete implementation of the IPlanningAgent interface.
    This agent is responsible for matching and execution of the routes defined in the `application_router`,
    which is a state machine.

    In abstract terms, the planning agent builds up a series of `ChatActions` to be executed by a bot API
    client.
    """

    def __init__(self, router: Router):
        self.router = router

    @staticmethod
    def _get_shared_parameters(context):
        """
        Returns the rendering and condition evaluation environment for Jinja2 templates
        """

        def chance(value: float) -> bool:
            return random.random() < value

        return dict(
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
            get=lambda key: context.get(key, None),
            formal=context.user.formal_address,
            informal=not context.user.formal_address,
            chance=chance,
            month=lambda n: MONTHS.get(n),
            is_this_year=lambda y: y == datetime.datetime.now().year
        )

    @staticmethod
    def _create_composer(context):
        """
        Creates a ResponseComposer instance with shared parameters
        """
        params = PlanningAgent._get_shared_parameters(context)
        return ResponseComposer(
            context.user,
            SelectiveTemplateLoader(
                params,
                template_selector=LeastRecentlyUsedSelector(context)),
            TemplateRenderer(params)
        )

    def build_next_actions(self, context: Context) -> Union[ResponseComposer, None]:
        u = context.last_user_utterance

        composer = self._create_composer(context)

        text = f'"{u.text[:40]}"' if u.text else ''
        log.info(f'Incoming message: {text}, {u}')
        log.debug(f'Current dialog states: {context.dialog_states}')

        # Execute every matching stateless handler first
        for handler in self.router.iter_stateless_matches(u):
            try:
                if handler.callback(composer, context):
                    log.debug(f"Stateless handler triggered: {handler}")
            except StopPropagation:
                # Some handlers may stop the propagation of the update through the chain of state handlers
                if composer.is_empty:
                    log.error("StopPropagation was raised but no chat actions were constructed.")
                    return
                self._log_actions(composer)
                return composer

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

        if isinstance(next_state, ResponseComposer):
            # Lambdas return the senctence composer, which we don't need (call by reference)
            next_state = None

        if next_state is not None:
            # Handlers return a tuple with the next state, with an integer determining the lifetime of this state as
            # the last tuple value.
            # For example: `("asking", "do_something", 3)`  <-- lifetime of 3 incoming utterances
            context.dialog_states.put(next_state)
            return composer

        self._log_actions(composer)
        return composer

    @staticmethod
    def _log_actions(composer):
        text = ', then '.join(f'"{x.render()}"' for x in composer.collect_actions())
        log.debug(f'Sending {text}')


class LeastRecentlyUsedSelector(TemplateSelector):
    """
    Selects the template that was used the least when there are multiple
    valid choices to select from.
    Used the KV-store of a user's context to save the counter.
    """

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
        self.context['used_templates'] = used_templates
        return selection
