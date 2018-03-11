import os
import time
from pprint import pprint
from threading import Thread
from typing import Callable, List

from flask import Flask, request
from logzero import logger
from telegram import *
from telegram import ChatAction as TelegramChatAction, Update as TelegramUpdate
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

import utils
from clients.botapiclients import IBotAPIClient
from core import ChatAction
from corpus.media import get_file_by_media_id
from model import User
from model.update import Update


class TelegramClient(IBotAPIClient):

    def __init__(self, app: Flask, webhook_url, token, test_mode=False):
        self._webhook_url = webhook_url
        self._app = app
        self._token = token

        self.updater = None  # type: Updater
        self.bot = None  # type: Bot
        self._test_mode = test_mode
        self._running = False
        self.__threads = list()

    @property
    def client_name(self):
        return 'telegram'

    def unify_update(self, update: TelegramUpdate):
        ud = Update()
        ud.original_update = update
        ud.client_name = self.client_name

        if update.callback_query:
            ud.payload = update.callback_query.data

        ud.user, created = User.get_or_create(telegram_id=update.effective_user.id)
        if created:
            ud.user.save()

        media_id = None
        if update.effective_message.photo:
            media_id = update.effective_message.photo[-1].file_id
        elif update.effective_message.video:
            media_id = update.effective_message.video.file_id
        elif update.effective_message.document:
            media_id = update.effective_message.document.file_id

        if media_id:
            file = self.bot.get_file(media_id)
            filename = os.path.split(file.file_path)[-1]
            ud.media_location = self.bot.get_file(media_id).download(
                custom_path=os.path.join(ud.user.media_folder, filename))
            print(ud.media_location)

        ud.message_id = update.effective_message.message_id
        ud.message_text = update.effective_message.text
        if update.effective_message.voice:
            ud.voice_id = update.effective_message.voice.file_id
        ud.datetime = update.effective_message.date
        return ud

    def perform_action(self, actions: List[ChatAction]):
        for i, action in enumerate(actions):
            if action.show_typing:
                self.bot.send_chat_action(action.peer.telegram_id, TelegramChatAction.TYPING, timeout=20)
            if action.delay:
                time.sleep(action.delay.value)

            markup = None
            if action.action_type == ChatAction.Type.ASKING_QUESTION:
                if action.choices:
                    buttons = [KeyboardButton(x) for x in action.choices]
                    markup = ReplyKeyboardMarkup(utils.build_menu(buttons, 3),
                                                 resize_keyboard=True,
                                                 one_time_keyboard=True,
                                                 selective=True)
                else:
                    if i < len(actions):
                        markup = ReplyKeyboardRemove()
                    else:
                        markup = ForceReply()
            elif action.action_type == ChatAction.Type.SENDING_MEDIA:
                return self.send_media(action.peer, action.media_id, action.render())

            text = action.render()
            self.send_message(peer=action.peer, text=text, markup=markup)

    def _init_thread(self, target, *args, **kwargs):
        thr = Thread(target=target, args=args, kwargs=kwargs)
        thr.start()
        self.__threads.append(thr)

    def initialize(self):
        self.updater = Updater(token=self._token, request_kwargs={'read_timeout': 10, 'connect_timeout': 7})
        self.bot = self.updater.bot

    def _webhook_endpoint(self):
        data = request.get_json()
        update = TelegramUpdate.de_json(data, self.updater.bot)
        self.updater.update_queue.put(update)

        return 'OK'

    def start_listening(self):
        # Start ptb threads
        self.updater.job_queue.start()
        self._init_thread(self.updater.dispatcher.start)

        if self._test_mode:
            self.updater.start_polling()
            return

        # Construct URL and set webhook
        url = self._webhook_url + self._token
        self.bot.set_webhook(url)
        self._app.add_url_rule(f"/{self._token}",
                               view_func=self._webhook_endpoint,
                               methods=['POST', 'GET'])

    def stop_listening(self):
        self.updater.job_queue.stop()
        self.updater.dispatcher.stop()
        self.updater.stop()

    def set_start_handler(self, callback: Callable):
        self.updater.dispatcher.add_handler(
            CommandHandler(
                "start",
                lambda bot, update: callback(self, self.unify_update(update))
            ))

    def add_plaintext_handler(self, callback: Callable):
        self.updater.dispatcher.add_handler(
            MessageHandler(
                Filters.text,
                lambda bot, update: callback(self, self.unify_update(update))
            ))

    def add_voice_handler(self, callback):
        self.updater.dispatcher.add_handler(
            MessageHandler(
                Filters.voice,
                lambda bot, update: callback(self, self.unify_update(update))
            )
        )

    def add_media_handler(self, callback):
        self.updater.dispatcher.add_handler(
            MessageHandler(
                (Filters.document | Filters.photo | Filters.video),
                lambda bot, update: callback(self, self.unify_update(update))
            )
        )

    def download_voice(self, voice_id, path):
        filepath = os.path.join(path, 'voice.ogg')
        voice = self.bot.get_file(voice_id)
        voice.download(filepath)
        return filepath

    def send_message(self, peer: User, text: str, markup=None):
        """
        Sends a markdown-formatted message to the `recipient`.
        """
        self.bot.send_message(peer.telegram_id, text, parse_mode=ParseMode.HTML,
                              reply_markup=markup, timeout=20)

    def send_media(self, peer: User, media_id: str, caption: str = None):
        filepath = get_file_by_media_id(media_id)
        ext = os.path.splitext(filepath)[1]

        file = open(filepath, 'rb')
        if ext == '.mp4':
            # GIF
            return self.bot.send_document(peer.telegram_id, file, caption=caption, timeout=20)
        elif ext in ('.jpg', '.jpeg', '.png'):
            return self.bot.send_photo(peer.telegram_id, file, caption=caption, timeout=20)
        elif ext == '.webp':
            msg = self.bot.send_sticker(peer.telegram_id, file, timeout=20)
            if caption:
                self.send_message(peer, caption, timeout=20)
            return msg

    def show_typing(self, user):
        self.bot.send_chat_action(user.telegram_id, TelegramChatAction.TYPING)

    def add_error_handler(self, callback: Callable):
        self.updater.dispatcher.logger = logger
        self.updater.dispatcher.add_error_handler(callback)
