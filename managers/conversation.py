from typing import List

from clients.botapiclients import IBotAPIClient
from clients.nlpclients import NLPEngine
from managers.context import ContextManager
from managers.planning import PlanningAgent
from model.update import Update


class ConversationManager:
    def __init__(self, bot_clients: List[IBotAPIClient], nlp_client: NLPEngine):
        self.bots = bot_clients
        self.nlp = nlp_client

        self.context_manager = ContextManager()
        self.planning_agent = PlanningAgent(self.context_manager)

        for bot in bot_clients:
            bot.add_plaintext_handler(self.update_received)

    def __get_client_by_name(self, client_name):
        return next(x for x in self.bots if client_name == x.client_name)

    def update_received(self, bot, update: Update):
        # Parse intents and entities
        self.nlp.insert_understanding(update)

        # Hand parameters to ContextManager
        self.context_manager.add_update(update)

        # Ask PlanningAgent what to do next

        # Generate response

        # Send response to user
        bot.send_message(update.user, f"Intents: *{update.intents}*"
                                      f"\nParameters: *{update.parameters}*"
                                      f"\nContexts: *{update.contexts}*")

        # Update ContextManager
        pass
