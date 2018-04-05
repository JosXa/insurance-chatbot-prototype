import threading
import time
from typing import List

from twilio.rest import Client as TwilioClient

from clients.botapiclients import BotAPIClient
from core import ChatAction
from model import User


class SMSClient(BotAPIClient):
    """
    Integration with Twilio to provide SMS capabilities.

    TODO: Currently not operational. This is an experiment and left as an exercise for the reader.
    """

    def __init__(self, access_token, account_sid):
        self.client = TwilioClient(account_sid, access_token)

    @property
    def client_name(self):
        return 'sms'

    def initialize(self):
        pass

    def _listener_thread(self):
        while True:
            # Get all messages
            all_messages = self.client.messages.list()
            print('There are {} messages in your account.'.format(len(all_messages)))
            for message in all_messages:
                self.unify_update(message)
            time.sleep(3)

    def start_listening(self):
        thr = threading.Thread(target=self._listener_thread)
        thr.start()

    def add_plaintext_handler(self, callback):
        pass

    def set_start_handler(self, callback):
        pass

    def _send_message(self, recipient: User, text: str, markup):
        pass

    def add_error_handler(self, callback):
        pass

    def unify_update(self, update):
        pass

    def perform_actions(self, actions: List[ChatAction]):
        print('performing actions in sms client')
        message = self.client.messages.create(
            to="+491728656978",
            from_="+15017250604",
            body="Hello from Python!")

        print(message.sid)

    def add_voice_handler(self, callback):
        pass

    def add_media_handler(self, callback):
        pass

    def show_typing(self, user):
        pass

    def download_voice(self, voice_id, filepath):
        pass
