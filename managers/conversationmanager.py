from typing import List

from fbmq import Event as FacebookEvent
from telegram import Update as TelegramUpdate

from clients.botapiclients import IBotAPIClient
from clients.common.update import Update
from clients.nlpclients import NLPEngine


class ConversationManager:
    def __init__(self, bot_clients: List[IBotAPIClient], nlp_client: NLPEngine):
        self.bots = bot_clients
        self.nlp = nlp_client

        for bot in bot_clients:
            bot.add_plaintext_handler(self.update_received)

    def __get_client_by_name(self, client_name):
        return next(x for x in self.bots if client_name == x.client_name)

    def update_received(self, bot, update: Update):
        # Parse intents and entities
        self.nlp.insert_understanding(update)

        # Hand parameters to ContextManager

        # Ask PlanningAgent what to do next

        # Generate response

        # Send response to user
        bot.send_message(update.user, f"Intents: *{update.intents}*\nParameters: "
                                      f"*{update.parameters}*")

        # Update ContextManager
        pass
