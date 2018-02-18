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
from tests.recorder import ConversationRecorder

threads = list()  # type: List[Thread]

USER_SEQ = dict()


def error_handler(bot, update, error):
    logger.exception(error)


def test_handler_fb(client, event):
    sender_id = event.sender_id
    recipient_id = event.recipient_id
    time_of_message = event.timestamp
    message = event.message

    seq = message.get("seq", 0)
    message_id = message.get("mid")
    app_id = message.get("app_id")
    metadata = message.get("metadata")

    message_text = message.get("text")
    message_attachments = message.get("attachments")
    quick_reply = message.get("quick_reply")

    seq_id = sender_id + ':' + recipient_id
    if USER_SEQ.get(seq_id, -1) >= seq:
        print("Ignore duplicated request")
        return None
    else:
        USER_SEQ[seq_id] = seq

    if quick_reply:
        quick_reply_payload = quick_reply.get('payload')
        print("quick reply for message %s with payload %s" % (message_id, quick_reply_payload))

        client.page.send(sender_id, "Quick reply tapped")

    if message_text:
        client.send_message(sender_id, message_text)
    elif message_attachments:
        client.send_message(sender_id, "Message with attachment received")


def main():
    migrate.reset_answers()  # TODO

    app = Flask(__name__)

    @app.route('/media/<mimetype>/<media_id>.<ext>', methods=['GET'])
    def media_endpoint(mimetype, media_id, ext):
        filepath = get_file_by_media_id(media_id)
        send_file(filepath, mimetype=f'{mimetype}/{ext}')

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

    DialogManager([telegram_client, facebook_client], dialogflow_client, conversation_recorder, voice_client)
    # DialogManager([sms_client, telegram_client, facebook_client], dialogflow_client, conversation_recorder)

    # sms_client.start_listening()
    telegram_client.start_listening()
    facebook_client.start_listening()

    if settings.TEST_MODE:
        logger.info("Listening...")
        telegram_client.updater.idle()
    else:
        app.run(host='0.0.0.0', port=settings.PORT)


if __name__ == '__main__':
    main()
