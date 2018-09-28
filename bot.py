from threading import Thread
from typing import List

from flask import Flask, send_file
from logzero import logger as log
from redis import StrictRedis

import settings
from clients.facebook import FacebookClient
from clients.nluclients import DialogflowClient
from clients.telegram import TelegramClient
from clients.telegramsupport import TelegramSupportChannel
from clients.voice import VoiceRecognitionClient
from core import ChatAction
from core.context import ContextManager, States
from core.dialogmanager import DialogManager
from core.recorder import ConversationRecorder
from corpus.media import get_file_by_media_id
from logic.planning import PlanningAgent
from logic.rules.dialogcontroller import application_router


def main():
    app = Flask(__name__)

    @app.route('/ping', methods=['GET'])
    def ping():
        return "Pong"

    # Register a media endpoint for clients that cannot upload images, videos etc. but instead only work with URLs
    @app.route('/media/<mimetype>/<media_id>.<ext>', methods=['GET'])
    def media_endpoint(mimetype, media_id, ext):
        filepath = get_file_by_media_id(media_id)
        return send_file(filepath, mimetype=f'{mimetype}/{ext}')

    # Initialize redis cache
    redis = StrictRedis.from_url(settings.REDIS_URL)

    # Initialize bot api client for Facebook Messenger
    facebook_client = FacebookClient(
        app=app,
        token=settings.FACEBOOK_ACCESS_TOKEN
    )
    facebook_client.initialize()

    # Initialize bot api client for Telegram Messenger
    telegram_client = TelegramClient(
        app=app,
        webhook_url=settings.APP_URL,
        token=settings.TELEGRAM_ACCESS_TOKEN,
        test_mode=settings.DEBUG_MODE
    )
    telegram_client.initialize()

    # sms_client = SMSClient(
    #     settings.TWILIO_ACCESS_TOKEN,
    #     settings.TWILIO_ACCOUNT_SID
    # )
    # sms_client.initialize()

    # Register a conversation logging channel on Telegram. This is an actual "channel" in Telegram terminology.
    support_client = TelegramSupportChannel(
        telegram_bot=telegram_client.bot,
        channel_id=settings.SUPPORT_CHANNEL_ID
    )

    # Initialize NLU and SLR clients
    dialogflow_client = DialogflowClient(settings.DIALOGFLOW_ACCESS_TOKEN)
    voice_client = VoiceRecognitionClient()

    # Create recorder for all conversations with the bot. This will publish to the support channel from above if the
    # custom `publish_trigger` condition is met.
    conversation_recorder = None
    if settings.ENABLE_CONVERSATION_RECORDING:

        def publish_trigger(_update, actions: List[ChatAction], _dialog_states) -> bool:
            if any('preview_claim' in a.intents for a in actions):
                return True
            return False

        conversation_recorder = ConversationRecorder(
            telegram_client.bot,
            support_channel=support_client,
            publish_trigger=publish_trigger
        )

    # Initialize planning agent that holds the core logic of creating context-sensitive responses
    planning_agent = PlanningAgent(router=application_router)

    # Initialize dialog management collection that will steer the main control flow when users interact with the bots
    DialogManager(
        context_manager=ContextManager(initial_state=States.SMALLTALK, redis=redis),
        bot_clients=[telegram_client, facebook_client],
        nlu_client=dialogflow_client,
        planning_agent=planning_agent,
        recorder=conversation_recorder,
        voice_recognition_client=voice_client,
        support_channel=support_client
    )

    # Actually start the application
    if settings.DEBUG_MODE:
        host = 'localhost'
        log.info(f"Listening in debug mode on {host}:{settings.PORT}...")
        Thread(
            target=app.run,
            name='Debug App',
            kwargs=dict(
                host=host,
                port=settings.PORT,
                debug=True,
                use_reloader=False
            )
        ).start()
        # long polling
        telegram_client.updater.idle()
    else:
        # webhooks
        log.info("Listening...")
        app.run(host='0.0.0.0', port=settings.PORT)


if __name__ == '__main__':
    main()
