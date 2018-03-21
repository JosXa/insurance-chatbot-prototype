import logging
import time

import logzero
from telethon import TelegramClient, events

from core import ChatAction

logzero.setup_logger('telethon').setLevel(level=logging.WARNING)


class Response:
    def __init__(self, text):
        self.text = text


class NoResponseReceived(Exception):
    pass


class IntegrationTestBase(object):

    def __init__(self):
        api_id = 34057
        api_hash = 'a89154bb0cde970cae0848dc7f7a6108'
        phone = '+491728656978'

        self.client = TelegramClient('josxa', api_id, api_hash, update_workers=4)
        self.client.start(phone)

        self._live_mode = False

        self._last_response = None
        self.client.add_event_handler(self.event_handler, events.NewMessage(
            chats=('@InsuranceBaBot', '@josxasandboxbot'), incoming=True))

    @property
    def live_mode(self):
        return self._live_mode

    @live_mode.setter
    def live_mode(self, value):
        self._live_mode = value
        self._peer = self.client.get_input_entity("@InsuranceBABot" if self._live_mode else "@josxasandboxbot")

    def disconnect(self):
        self.client.disconnect()

    def event_handler(self, event: events.NewMessage.Event):
        self._last_response = Response(text=event.text)

    def send_message_get_response(self, text) -> Response:
        self._last_response = None

        self.client.send_message(self._peer, text)

        timeout = 10  # seconds
        count = 0
        while self._last_response is None:
            if count >= timeout:
                raise NoResponseReceived()
            time.sleep(0.4)

        # response received - wait a bit to see if the bot keeps sending messages
        max_sleep_time = ChatAction.Delay.VERY_LONG.value + 0.3
        last_msg = self._last_response
        parts = [last_msg.text]

        time.sleep(max_sleep_time)
        while self._last_response != last_msg:
            last_msg = self._last_response
            parts.append(last_msg.text)
            time.sleep(max_sleep_time)

        del self._last_response
        return Response(', then '.join(f'"{x}"' for x in parts))
