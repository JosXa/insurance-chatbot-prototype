from pprint import pprint
from typing import List

from clients.botapiclients import IBotAPIClient
from fbmq import Event as FacebookEvent
from telegram import Update as TelegramUpdate

from clients.common.update import Update
from clients.nlpclients import NLPEngine
from model import User


class ConversationManager:
    def __init__(self, bot_clients: List[IBotAPIClient], nlp_client: NLPEngine):
        self.bots = bot_clients
        self.nlp = nlp_client

        for bot in bot_clients:
            bot.add_plaintext_handler(self._unify_update)

    def _unify_update(self, update):
        if isinstance(update, TelegramUpdate):
            self.update_received(Update.from_telegram_update(update))
        elif isinstance(update, FacebookEvent):
            self.update_received(Update.from_facebook_event(update))
        else:
            raise ValueError(f"Invalid update type: {type(update)}")

    def update_received(self, update: Update):
        # TODO

        # Parse intents and entities
        nlp_response = self.nlp.text_request(update.message_text)
        pprint(nlp_response)

        # Add intents and entities to Update

        # Hand parameters to ContextManager

        # Ask PlanningAgent what to do next

        # Generate response

        # Send response to user

        # Update ContextManager
        pass
