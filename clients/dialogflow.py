import json
from pprint import pprint

import apiai

from model import User
from settings import DIALOGFLOW_ACCESS_TOKEN

ai = apiai.ApiAI(DIALOGFLOW_ACCESS_TOKEN)


class DialogflowClient:
    def __init__(self):
        pass

    def text_request(self, user: User, text: str):
        request = ai.text_request()

        request.lang = 'de'
        request.session_id = user.id
        request.query = text

        response = request.getresponse()
        return json.loads(response.read())

    def user_entities_request(self, user):
        request = ai.user_entities_request()

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
