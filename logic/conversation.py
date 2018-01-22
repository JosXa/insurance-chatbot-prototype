from typing import List, TypeVar

from logic.context import UserContexts
from logic.planning import PlanningAgent
from logic.rules import rule_controller
from logic.understanding import MessageUnderstanding
from model import Update
from tests.recorder import ConversationRecorder

NLPEngine = TypeVar('NLPEngine')
IBotAPIClient = TypeVar('IBotAPIClient')


class ConversationManager:
    """
    Enriches incoming updates with a MessageUnderstanding and lets the PlanningAgent decide on the next actions to
    perform.
    """

    def __init__(self, bot_clients: List[IBotAPIClient], nlp_client: NLPEngine, recorder: ConversationRecorder = None):
        self.bots = bot_clients
        self.nlp = nlp_client
        self.controller = rule_controller
        self.recorder = recorder

        self.context_manager = UserContexts()
        self.planning_agent = PlanningAgent(self.controller)

        for bot in bot_clients:
            bot.add_plaintext_handler(self.update_received)
            bot.set_start_handler(self.start_callback)

    def __get_client_by_name(self, client_name: str) -> IBotAPIClient:
        return next(x for x in self.bots if client_name == x.client_name)

    def start_callback(self, bot: IBotAPIClient, update: Update):
        update.understanding = MessageUnderstanding(
            text=update.message_text,
            intent='start')
        self._process_update(bot, update)

    def update_received(self, bot: IBotAPIClient, update: Update):
        self.nlp.insert_understanding(update)
        self._process_update(bot, update)

    def _process_update(self, bot, update):
        context = self.context_manager.add_incoming_update(update)
        next_response = self.planning_agent.build_next_actions(context)

        actions = next_response.collect_actions()

        if self.recorder:
            self.recorder.record_dialog(update, actions)
            self.recorder.save()

        bot.perform_actions(actions)
        context.add_actions(actions)
