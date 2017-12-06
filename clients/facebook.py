# -*- coding: utf-8 -*-
import logging
from threading import Thread

from fbmq import Page, NotificationType
from flask import Flask, request

import settings
from clients.botapiclients import IBotAPIClient

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)

app = Flask(__name__)


class FacebookClient(IBotAPIClient):
    def __init__(self, token):
        self._token = token

        self._page = None  # type: Page

    def _authentication(self):
        all_args = request.args
        if 'hub.challenge' in all_args:
            return all_args['hub.challenge']

    def _webhook(self):
        self._page.handle_webhook(request.get_data(as_text=True))
        return "ok"

    def __shutdown_server(self):
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()

    def initialize(self):
        self._page = Page(self._token)
        self._page.show_starting_button("START_BOT")

        # Add webhook handlers
        app.add_url_rule('/', 'index', self._authentication, methods=['GET'])
        app.add_url_rule('/', 'request', self._webhook, methods=['POST'])

        # try:
        #     self.page.send(1441586482543309, "Up and running.")
        # except:
        #     print("Could not contact 1441586482543309.")

    def start_listening(self):
        # TODO: break control
        print('before')
        app.run(host='0.0.0.0', port=settings.TELEGRAM_WEBHOOK_PORT)
        print('after')

    def stop_listening(self):
        self.__shutdown_server()

    def add_plaintext_handler(self, callback):
        self._page._webhook_handlers['message'] = lambda cb: callback(self, cb)

    def send_message(self, recipient_id, text):
        self._page.send(recipient_id, text, callback=None,
                        notification_type=NotificationType.REGULAR)


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
