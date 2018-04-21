import os
from typing import List

import time
from logzero import logger as log

import settings
from appglobals import ROOT_DIR
from clients.botapiclients import BotAPIClient
from clients.nluclients import NLUEngine
from clients.supportchannel import SupportChannel
from clients.voice import VoiceRecognitionClient
from core import ChatAction
from core.context import ContextManager
from core.planningagent import IPlanningAgent
from core.recorder import ConversationRecorder
from core.understanding import MessageUnderstanding
from logic.intents import MEDIA_INTENT
from logic.responsecomposer import NOT_SET
from model import Update


class DialogManager:
    """
    Responsible for handling incoming `Updates` and generating a response.

    Enriches incoming updates with a `MessageUnderstanding` and lets the `PlanningAgent` decide on which actions to
    perform next. Then calls `perform_actions` on the respective client with the laid-out `ChatActions`.
    """

    def __init__(self,
                 context_manager: ContextManager,
                 bot_clients: List[BotAPIClient],
                 nlu_client: NLUEngine,
                 planning_agent: IPlanningAgent,
                 recorder: ConversationRecorder = None,
                 voice_recognition_client: VoiceRecognitionClient = None,
                 support_channel: SupportChannel = None
                 ):
        self.context_manager = context_manager
        self.bots = bot_clients
        self.nlp = nlu_client
        self.recorder = recorder
        self.voice = voice_recognition_client
        self.planning_agent = planning_agent
        self.support_channel = support_channel

        for bot in bot_clients:
            bot.set_start_handler(self.start_callback)
            bot.add_plaintext_handler(self.text_update_received)
            bot.add_voice_handler(self.voice_received)
            bot.add_media_handler(self.media_received)

            bot.start_listening()

    def __get_client_by_name(self, client_name: str) -> BotAPIClient:
        return next(x for x in self.bots if client_name == x.client_name)

    def start_callback(self, bot: BotAPIClient, update: Update):
        update.understanding = MessageUnderstanding(
            text=update.message_text,
            intent='start')
        self._process_update(bot, update)

    def voice_received(self, bot: BotAPIClient, update: Update):
        bot.show_typing(update.user)

        path = os.path.join(ROOT_DIR, 'tmp')
        filepath = bot.download_voice(update.voice_id, path)

        converted = self.voice.convert_audio_ffmpeg(filepath, os.path.join(path, 'voice.flac'))

        text = self.voice.recognize(converted)
        if text is None:
            log.warning("Could not recognize user input.")
            return

        update.message_text = text
        log.debug(f"Voice message received: {text}")

        self.text_update_received(bot, update)

    def media_received(self, bot: BotAPIClient, update: Update):
        update.understanding = MessageUnderstanding(None, MEDIA_INTENT, media_location=update.media_location)
        self._process_update(bot, update)

    def text_update_received(self, bot: BotAPIClient, update: Update):
        self.nlp.insert_understanding(update)
        self._process_update(bot, update)

    def _process_update(self, bot: BotAPIClient, update: Update):
        print()  # newline on incoming request makes the logs more readable
        context = self.context_manager.add_incoming_update(update)

        try:
            try:
                next_response = self.planning_agent.build_next_actions(context)
            except ForceReevaluation:
                # Some handlers require to reevaluate the template parameters (only once)
                next_response = self.planning_agent.build_next_actions(context)
            if next_response is None:
                return
            actions = next_response.collect_actions()
        finally:
            context.dialog_states.update_step()

        if self.recorder:
            self.recorder.record_dialog(update, actions, context.dialog_states)

        if settings.NO_DELAYS:
            # No message delays while debugging
            for a in actions:
                a.delay = None

        # Assign default value if no delay was set
        for a in actions:
            if a.delay is NOT_SET:
                a.delay = ChatAction.Delay.MEDIUM

        if settings.DEMO_MODE:
            time.sleep(2.3)

        try:
            bot.perform_actions(actions)
        except Exception as e:
            log.error("Error while performing chat action:")
            log.exception(e)

        context.add_actions(actions)
        update.save()


class ForceReevaluation(Exception):
    """
    Raised when a handler changes e.g. context state and needs a refreshed set
    of rendering parameters.
    """
    pass


class StopPropagation(Exception):
    """
    Raised when an update handler decides that the update should not be moved forward in the chain of matching handlers
    """
    pass
