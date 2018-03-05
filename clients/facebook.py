# -*- coding: utf-8 -*-
import datetime
import os
import time
from pprint import pprint
from typing import Callable, List

from fbmq import Attachment, Event, Page, QuickReply
from flask import request

import settings
from clients.botapiclients import IBotAPIClient
from core import ChatAction
from corpus.media import get_file_by_media_id
from model import Update, User


class FacebookClient(IBotAPIClient):

    def __init__(self, app, token):
        self._app = app
        self._token = token

        self._page = None  # type: Page
        self._error_handler = None  # type: Callable[Exception]

    @property
    def client_name(self):
        return 'facebook'

    def unify_update(self, event: Event, payload: str = None):
        ud = Update()
        ud.original_update = event
        ud.client_name = self.client_name
        ud.message_id = event.message_mid
        ud.datetime = datetime.datetime.fromtimestamp(event.timestamp / 1000.0)

        ud.payload = payload

        ud.user, created = User.get_or_create(facebook_id=event.sender_id)
        if created:
            ud.user.save()

        if event.message_attachments:
            pprint(event.message_attachments)

        if hasattr(event, 'message_text'):
            ud.message_text = event.message_text
        return ud

    def initialize(self):
        self._page = Page(self._token)
        self._page.show_starting_button("START_BOT")

        # Add webhook handlers
        self._app.add_url_rule('/', 'index', self._authentication, methods=['GET'])
        self._app.add_url_rule('/', 'request', self._webhook, methods=['POST'])

    def perform_action(self, actions: List[ChatAction]):
        for action in actions:
            user_id = action.peer.facebook_id

            if action.show_typing:
                self.show_typing(user_id)
            if action.delay:
                time.sleep(action.delay.value)

            quick_replies = None
            if action.action_type == ChatAction.Type.ASKING_QUESTION:
                if action.choices:
                    quick_replies = [QuickReply(title=x, payload=f"test_{x}") for x in action.choices]
            elif action.action_type == ChatAction.Type.SENDING_MEDIA:
                self.send_media(action.peer, action.media_id, action.render())

            self._page.send(user_id, action.render(), quick_replies=quick_replies)

    @staticmethod
    def _authentication():
        all_args = request.args
        if 'hub.challenge' in all_args:
            return all_args['hub.challenge']

    def _webhook(self):
        self._page.handle_webhook(request.get_data(as_text=True))
        return "ok"

    @staticmethod
    def __shutdown_server():
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()

    def start_listening(self):
        pass

    def stop_listening(self):
        self.__shutdown_server()

    def set_start_handler(self, callback):
        @self._page.callback(['START_BOT'])
        def start_handler(payload, event):
            callback(self, self.unify_update(event, payload))

    def add_plaintext_handler(self, callback):
        def filter(event):
            if not event.message_text:
                return
            return callback(self, self.unify_update(event))

        self._page.set_webhook_handler('message', filter)

    def add_voice_handler(self, callback):
        pass

    def download_voice(self, voice_id, filepath):
        pass

    def send_media(self, peer, media_id, param):
        filepath = get_file_by_media_id(media_id)
        ext = os.path.splitext(filepath)[1]

        # Host the file

        if ext == '.mp4':
            # GIF
            pass
        elif ext in ('.jpg', '.jpeg', '.png'):
            image_url = settings.APP_URL + f'/media/image/{media_id}.{ext}'
            return self._page.send(peer.facebook_id, Attachment.Image(image_url))
        elif ext == '.webp':
            pass  # sticker
            # msg = self.bot.send_sticker(peer.telegram_id, file)
            # if caption:
            #     self.send_message(peer, caption)
            # return msg

    def show_typing(self, user_id):
        self._page.typing_on(user_id)

    def add_error_handler(self, callback):
        self._error_handler = callback


"""
import logging
import random

from decouple import config
from fbmq import QuickReply, Event
from fbpage import page
from flask import request, Flask

import settings
from model import User
# parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# os.sys.path.insert(0, parentdir)
log = logging.getLogger(__name__)

app = Flask(__name__)

page.show_starting_button("START_BOT")


@app.route('/', methods=['POST'])
def webhook():
    page.handle_webhook(request.get_data(as_text=True))
    return "ok"


@page.handle_delivery
def delivery(event: Event):
    pass


# @page.handle_referral
# def referral(event: Event):
#     user = User.from_event(event)
#     user.referral = event.referral_ref
#     user.save()
#     start(None, event)


@page.callback(['START_BOT'])
def start_handler(payload, event):
    user = User.from_event(event)

    quick_replies = [
        QuickReply(title="Yeah, sure", payload="yes-more-info"),
    ]

    page.send(user.sender_id,
              "STARTED",
              quick_replies=quick_replies)


@page.handle_message
def message_handler(event: Event):
    query = event.message_text.lower()

    if query == 'start':
        return start(None, event)
    elif query == 'love':
        page.send(1433118220058887, random.choice(loveyous))
        return

        # start(None, event)

def start():
    log.info("Listening...")
    app.run(host=config('WEBHOOK_URL'), port=config('WEBHOOK_PORT'), ssl_context=(
        '/home/joscha/cert/josxa.jumpingcrab.com/fullchain.pem',
        '/home/joscha/cert/josxa.jumpingcrab.com/privkey.pem'))
"""
