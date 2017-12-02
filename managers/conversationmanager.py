from typing import List

from clients.botapiclients import IBotAPIClient


class ConversationManager:
    def __init__(self, clients: List[IBotAPIClient], dialogflow):
        self.clients = clients
        self.dialogflow = dialogflow

