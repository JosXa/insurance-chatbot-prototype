import logging
import time
from datetime import datetime, timedelta
from pprint import pprint

import logzero
from telethon import TelegramClient, events
from telethon.events import NewMessage
from telethon.tl.functions.messages import DeleteHistoryRequest
from telethon.tl.types import ReplyKeyboardForceReply

import settings
from core import ChatAction
from util import paginate

logzero.setup_logger('telethon').setLevel(level=logging.WARNING)


class Response:
    def __init__(self, text, message_id, is_force_reply, buttons=None):
        self.text = text
        self.message_id = message_id
        self.is_force_reply = is_force_reply
        self.buttons = buttons or []

    @classmethod
    def from_event(cls, event: NewMessage.Event):
        markup = event.message.reply_markup
        force_reply = isinstance(markup, ReplyKeyboardForceReply)

        buttons = None
        if markup:
            if hasattr(markup, 'rows'):
                buttons = [x.text for x in markup.rows[0].buttons]
        if buttons:
            pprint(buttons)

        return cls(
            text=event.message.message,
            message_id=event.message.id,
            is_force_reply=force_reply,
            buttons=buttons
        )


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

    def event_handler(self, event):
        self._last_response = Response.from_event(event)

    def delete_history(self, max_id=None, full=False):
        if full:
            self.client(DeleteHistoryRequest(self._peer, max_id or 2147483647))
        else:

            for m in paginate(self.client.iter_messages(self._peer, limit=10000), 100):
                self.client.delete_messages(self._peer, m)

    def send_message_get_response(self, text, timeout=20, raise_=True, **kwargs) -> Response:
        """
        Sends a message to the bot and waits for the response.
        :param text: Message to send
        :param timeout: Timout in seconds
        :return:
        """
        self._last_response = None

        self.client.send_message(self._peer, text, **kwargs)

        end = datetime.now() + timedelta(seconds=timeout)
        while self._last_response is None:
            if datetime.now() > end:
                if raise_:
                    raise NoResponseReceived()
                return
            time.sleep(0.4)

        # response received - wait a bit to see if the bot keeps sending messages
        if settings.NO_DELAYS:
            sleep_time = 0.8
        else:
            sleep_time = ChatAction.Delay.VERY_LONG.value + (0.3 if self.live_mode else 0.8)
        last_msg = self._last_response

        time.sleep(sleep_time)
        while self._last_response != last_msg:
            last_msg = self._last_response
            time.sleep(sleep_time)

        del self._last_response

        # Only the last response matters
        return last_msg
