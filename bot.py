import os
from threading import Thread
from typing import List

from flask import Flask, send_file
from logzero import logger

import migrate
import settings
from clients.facebook import FacebookClient
from clients.nlpclients import DialogflowClient
from clients.telegram import TelegramClient
from clients.voice import VoiceRecognitionClient
from core.dialogmanager import DialogManager
from corpus.media import get_file_by_media_id
from logic.planning import PlanningAgent
from logic.rules.routing import controller
from tests.recorder import ConversationRecorder

threads = list()  # type: List[Thread]

USER_SEQ = dict()

if not os.path.exists('files'):
    os.makedirs('files')


def error_handler(bot, update, error):
    logger.exception(error)


def main():
    migrate.reset_answers()  # TODO

    app = Flask(__name__)

    @app.route('/media/<mimetype>/<media_id>.<ext>', methods=['GET'])
    def media_endpoint(mimetype, media_id, ext):
        print(mimetype, media_id, ext)
        filepath = get_file_by_media_id(media_id)
        print(filepath)
        return send_file(filepath, mimetype=f'{mimetype}/{ext}')

    # sms_client = SMSClient(
    #     settings.TWILIO_ACCESS_TOKEN,
    #     settings.TWILIO_ACCOUNT_SID
    # )
    # sms_client.initialize()

    facebook_client = FacebookClient(
        app,
        settings.FACEBOOK_ACCESS_TOKEN
    )
    facebook_client.initialize()

    telegram_client = TelegramClient(
        app,
        settings.APP_URL,
        settings.TELEGRAM_ACCESS_TOKEN,
        test_mode=settings.TEST_MODE
    )
    telegram_client.initialize()

    # telegram_client.add_plaintext_handler(test_handler_tg)
    # facebook_client.add_plaintext_handler(test_handler_fb)

    telegram_client.add_error_handler(error_handler)

    dialogflow_client = DialogflowClient(settings.DIALOGFLOW_ACCESS_TOKEN)
    voice_client = VoiceRecognitionClient()

    conversation_recorder = None
    if settings.ENABLE_CONVERSATION_RECORDING:
        conversation_recorder = ConversationRecorder(telegram_client.bot, settings.SUPPORT_CHANNEL_ID)

    planning_agent = PlanningAgent(controller=controller)

    DialogManager(
        bot_clients=[telegram_client, facebook_client],
        nlp_client=dialogflow_client,
        planning_agent=planning_agent,
        recorder=conversation_recorder,
        voice_recognition_client=voice_client
    )

    telegram_client.start_listening()
    facebook_client.start_listening()

    if settings.TEST_MODE:
        logger.info("Listening...")
        telegram_client.updater.idle()
    else:
        app.run(host='0.0.0.0', port=settings.PORT)


if __name__ == '__main__':
    main()
