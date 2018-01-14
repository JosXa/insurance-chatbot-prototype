from typing import List

from clients.botapiclients import IBotAPIClient
from clients.nlpclients import NLPEngine
from logic.context import UserContexts
from logic.planning import PlanningAgent
from model.update import Update


class ConversationManager:
    def __init__(self, bot_clients: List[IBotAPIClient], nlp_client: NLPEngine):
        self.bots = bot_clients
        self.nlp = nlp_client

        self.context_manager = UserContexts()

        for bot in bot_clients:
            bot.add_plaintext_handler(self.update_received)

    def __get_client_by_name(self, client_name: str) -> IBotAPIClient:
        return next(x for x in self.bots if client_name == x.client_name)

    def update_received(self, bot: IBotAPIClient, update: Update):
        self.nlp.insert_understanding(update)
        context = self.context_manager.add_incoming_update(update)

        agent = PlanningAgent(context)
        next_response = agent.build_next_actions()

        actions = next_response.collect_actions()

        bot.perform_actions(actions)
        context.add_outgoing(actions)

        del agent
