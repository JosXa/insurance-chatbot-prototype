# -*- coding: utf-8 -*-
import datetime
import os
import shutil
import time
from typing import Callable, List

import requests
from fbmq import Attachment, Event, Page, QuickReply
from flask import request
from logzero import logger as log

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
        self._plaintext_handlers = []  # type: List[Callable[Event]]
        self._voice_handlers = []  # type: List[Callable[Event]]

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
            try:
                voice = next(x for x in event.message_attachments if x.get('type') == 'audio')
                ud.voice_id = voice['payload']['url']
            except StopIteration:
                pass

        if hasattr(event, 'message_text'):
            ud.message_text = event.message_text
        return ud

    def initialize(self):
        self._page = Page(self._token)
        self._page.show_starting_button("START_BOT")

        # Add webhook handlers
        self._app.add_url_rule('/', 'index', self._authentication, methods=['GET'])
        self._app.add_url_rule('/', 'request', self._webhook, methods=['POST'])

        self._page.set_webhook_handler('message', self._message_handler)
        self._page.set_webhook_handler('delivery', self._delivery_handler)

    def _delivery_handler(self, event):
        delivery = event.delivery
        message_ids = delivery.get("mids")
        watermark = delivery.get("watermark")
        log.info(f"Message delivered: {message_ids} ({watermark})")

    def perform_action(self, actions: List[ChatAction]):
        for action in actions:
            try:
                user_id = action.peer.facebook_id

                if action.show_typing:
                    log.debug("User id: " + user_id)
                    self.show_typing(user_id)
                if action.delay:
                    # Facebook bots are very slow, shorten timeout
                    time.sleep(action.delay.value * 0.3)

                quick_replies = None
                if action.action_type == ChatAction.Type.ASKING_QUESTION:
                    if action.choices:
                        quick_replies = [QuickReply(title=x, payload=f"test_{x}") for x in action.choices[:10]]
                elif action.action_type == ChatAction.Type.SENDING_MEDIA:
                    res = self.send_media(action.peer, action.media_id, action.render())
                    print(res)
                    return

                self._page.send(
                    recipient_id=user_id,
                    message=action.render(),
                    quick_replies=quick_replies)
            finally:
                self.end_typing(user_id)

    @staticmethod
    def _authentication():
        all_args = request.args
        if 'hub.challenge' in all_args:
            return all_args['hub.challenge']
        log.info("Root request: " + all_args)
        return ''

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

    def _message_handler(self, event):
        for callback in self._plaintext_handlers:
            if not event.message_text:
                break
            callback(self, self.unify_update(event))
        for callback in self._voice_handlers:
            if not event.is_attachment_message:
                break
            if not any(x for x in event.message_attachments if x.get('type') == 'audio'):
                break
            callback(self, self.unify_update(event))

    def add_plaintext_handler(self, callback):
        self._plaintext_handlers.append(callback)

    def add_voice_handler(self, callback):
        self._voice_handlers.append(callback)

    def download_voice(self, voice_id, path):
        filepath = os.path.join(path, 'voice.mp4')
        r = requests.get(voice_id, stream=True)
        with open(filepath, 'wb') as f:
            shutil.copyfileobj(r.raw, f)
        return filepath

    def send_media(self, peer, media_id, caption):
        filepath = get_file_by_media_id(media_id)
        ext = os.path.splitext(filepath)[1]

        return  # TODO: broken

        if ext == '.mp4':
            video_url = settings.APP_URL + f'media/video/{media_id}{ext}'
            print(video_url)
            return self._page.send(peer.facebook_id, Attachment.Video(video_url))
        elif ext in ('.jpg', '.jpeg', '.png'):
            image_url = settings.APP_URL + f'media/image/{media_id}{ext}'
            return self._page.send(peer.facebook_id, Attachment.Image(image_url))
        elif ext == '.webp':
            pass  # sticker
            # msg = self.bot.send_sticker(peer.telegram_id, file)
            # if caption:
            #     self.send_message(peer, caption)
            # return msg

    def show_typing(self, user_id):
        try:
            self._page.typing_on(user_id)
        except:
            log.error("Turning typing indication on failed.")

    def end_typing(self, user_id):
        try:
            self._page.typing_off(user_id)
        except:
            log.error("Turning typing indication off failed.")

    def add_error_handler(self, callback):
        self._error_handler = callback
