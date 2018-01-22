import logging
import time
import unittest

from telethon import TelegramClient
from telethon.tl.types import UpdateShortMessage

logging.basicConfig(level=logging.DEBUG)
# For instance, show only warnings and above
logging.getLogger('telethon').setLevel(level=logging.WARNING)


class Response:
    def __init__(self, text):
        self.text = text


class NoResponseReceived(Exception):
    pass


class IntegrationTestBase(unittest.TestCase):
    __test__ = False

    def setUp(self):
        api_id = 34057
        api_hash = 'a89154bb0cde970cae0848dc7f7a6108'
        phone = '+491728656978'

        self.client = TelegramClient('josxa', api_id, api_hash, update_workers=4)
        self.client.connect()
        if not self.client.is_user_authorized():
            self.client.send_code_request(phone)
            self.client.sign_in(phone, input("Enter code: "))

        self._peer = self.client.get_input_entity("@InsuranceBABot")
        self._last_response = None
        self.client.add_update_handler(self._update_handler)

    def tearDown(self):
        self.client.disconnect()

    def _update_handler(self, update):

        if isinstance(update, UpdateShortMessage):
            print(f"New UpdateShortMessage from {update.user_id} (equals {self._peer.user_id}: "
                  f"{update.user_id == self._peer.user_id})")
            if update.user_id == self._peer.user_id:
                self._last_response = Response(text=update.message)

    def send_message_get_response(self, text) -> Response:
        self._last_response = None

        self.client.send_message(self._peer, text)

        timeout = 5  # seconds
        count = 0
        while self._last_response is None:
            if count >= timeout:
                raise NoResponseReceived()
            time.sleep(1)
        result = self._last_response
        del self._last_response
        return result
