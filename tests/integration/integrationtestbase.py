import logging
import time
import unittest

from telethon import TelegramClient, events
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
        self.client.start(phone)

        self._live_mode = False

        self._last_response = None
        self.client.add_event_handler(self._event_handler, events.NewMessage(chats=('@InsuranceBaBot',
                                                                                    '@josxasandboxbot')))

    @property
    def live_mode(self):
        return self._live_mode

    @live_mode.setter
    def live_mode(self, value):
        self._live_mode = value
        self._peer = self.client.get_input_entity("@InsuranceBABot" if self._live_mode else "@josxasandboxbot")

    def tearDown(self):
        self.client.disconnect()

    def _event_handler(self, event: events.NewMessage.Event):

        if event.sender.username == self._peer:
            self._last_response = Response(text=event.text)

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
