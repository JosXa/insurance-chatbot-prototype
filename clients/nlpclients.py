import json
from abc import ABCMeta, abstractmethod

import apiai

from model import User
from model.update import Update


class NLPEngine(metaclass=ABCMeta):
    @abstractmethod
    def text_request(self, user: User, text: str): pass

    @abstractmethod
    def get_user_entities(self, user: User): pass

    @abstractmethod
    def insert_understanding(self, update: Update): pass


class DialogflowClient(NLPEngine):
    def insert_understanding(self, update: Update):
        nlp_response = self.text_request(update.user, update.message_text)

        if nlp_response.get('result', None) is not None:
            nlu = nlp_response['result']
            # Add intents and entities to Update
            try:
                update.intents = nlu['metadata']['intentName']
                update.parameters = nlu['parameters']
                update.contexts = nlu['contexts']
                # TODO:  nlu['score'] ?
            except AttributeError:
                pass

    def __init__(self, token):
        self.ai = apiai.ApiAI(token)

    def text_request(self, user: User, text: str):
        request = self.ai.text_request()

        request.lang = 'de'
        request.session_id = user.id
        request.query = text

        response = request.getresponse()
        return json.loads(response.read())

    def get_user_entities(self, user):
        request = self.ai.user_entities_request()

        response = request.getresponse()
        return json.loads(response.read())

    @staticmethod
    def extract_entities(response: dict):
        pass

    @staticmethod
    def extract_action(response: dict):
        pass

    @staticmethod
    def extract_parameters(response: dict):
        pass

    @staticmethod
    def extract_status(response: dict):
        """
        Returns a tuple of (status_code, errorType)
        """
        return (response['status']['code'], response['status']['errorType'])
