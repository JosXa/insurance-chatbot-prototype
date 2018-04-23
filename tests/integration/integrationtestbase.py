import logging
import time
from datetime import datetime, timedelta
from pprint import pprint
from typing import Callable
from uuid import uuid4

import logzero
from telethon import TelegramClient, events
from telethon.events import NewMessage
from telethon.tl.functions.messages import DeleteHistoryRequest, SaveDraftRequest
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

        return cls(
            text=event.text,
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
        self._responses = {}
        self.client.add_event_handler(self.event_handler, events.NewMessage(
            chats=('@InsuranceBaBot', '@josxasandboxbot'), incoming=True))

    def set_draft(self, text, reply_to=None):
        return self.client(SaveDraftRequest(
            peer=self._peer,
            message=text,
            no_webpage=True,
            reply_to_msg_id=reply_to
        ))

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

    def send_message_get_response(self, text, timeout=20, raise_=True, min_wait_consecutive=None, **kwargs) -> Response:
        """
        Sends a message to the bot and waits for the response.
        :param text: Message to send
        :param timeout: Timout in seconds
        :return:
        """
        if min_wait_consecutive is None:
            min_wait_consecutive = ChatAction.Delay.VERY_LONG.value + (0.3 if self.live_mode else 0.8)

        return self._act_await_response(
            lambda: self.client.send_message(self._peer, text, **kwargs),
            NewMessage(incoming=True, chats=[self._peer]),
            timeout=timeout,
            raise_=raise_,
            min_wait_consecutive=min_wait_consecutive
        )

    def _act_await_response(self, action: Callable, event_builder: NewMessage, timeout=20, raise_=True,
                            min_wait_consecutive=5):

        id_ = uuid4()
        self._responses[id_] = None

        def await_(event):
            self._responses[id_] = Response.from_event(event)

        handler = self.client.add_event_handler(await_, event_builder)

        if action:
            action()

        # Wait `timeout` seconds for a response
        end = datetime.now() + timedelta(seconds=timeout)
        while self._responses[id_] is None:
            if datetime.now() > end:
                if raise_:
                    raise NoResponseReceived()
                return
            time.sleep(0.3)

        # response received - wait a bit to see if the bot keeps sending messages
        if settings.NO_DELAYS:
            sleep_time = 0.8
        else:
            sleep_time = min_wait_consecutive

        last_response = self._responses[id_]
        time.sleep(sleep_time)
        while self._responses[id_] != last_response:
            last_response = self._responses[id_]
            time.sleep(sleep_time)

        self.client.remove_event_handler(handler)
        result = self._responses.pop(id_)
        time.sleep(0.15)
        return result

    def wait_outgoing(self, text):
        no_markdown, _ = self.client._parse_message_text(text, 'markdown')
        result = self._act_await_response(
            lambda: self._act_await_response(
                None,
                NewMessage(outgoing=True, pattern=no_markdown),
                min_wait_consecutive=0,
                timeout=99999
            ),
            NewMessage(incoming=True, chats=[self._peer]),
            min_wait_consecutive=3
        )
        return result
