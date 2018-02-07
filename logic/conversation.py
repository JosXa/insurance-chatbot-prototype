import os
from typing import List

from logzero import logger

from appglobals import ROOT_DIR
from clients.botapiclients import IBotAPIClient
from clients.nlpclients import NLPEngine
from clients.voice import VoiceRecognitionClient
from logic.claimrules import controller
from logic.context import UserContexts
from logic.planning import PlanningAgent
from logic.understanding import MessageUnderstanding
from model import Update
from tests.recorder import ConversationRecorder


class ConversationManager:
    """
    Enriches incoming updates with a MessageUnderstanding and lets the PlanningAgent decide on the next actions to
    perform.
    """

    def __init__(self, bot_clients: List[IBotAPIClient], nlp_client: NLPEngine, recorder: ConversationRecorder =
    None, voice_recognition: VoiceRecognitionClient = None):
        self.bots = bot_clients
        self.nlp = nlp_client
        self.controller = controller
        self.recorder = recorder
        self.voice = voice_recognition

        self.context_manager = UserContexts()
        self.planning_agent = PlanningAgent(self.controller)

        for bot in bot_clients:
            bot.add_plaintext_handler(self.text_update_received)
            bot.add_voice_handler(self.voice_received)
            bot.set_start_handler(self.start_callback)

    def __get_client_by_name(self, client_name: str) -> IBotAPIClient:
        return next(x for x in self.bots if client_name == x.client_name)

    def start_callback(self, bot: IBotAPIClient, update: Update):
        update.understanding = MessageUnderstanding(
            text=update.message_text,
            intent='start')
        self._process_update(bot, update)

    def voice_received(self, bot: IBotAPIClient, update: Update):
        bot.show_typing(update.user)

        path = os.path.join(ROOT_DIR, 'assets', 'files')
        filepath = bot.download_voice(update.voice_id, path)

        converted = self.voice.convert_audio_ffmpeg(filepath, os.path.join(path, 'voice.flac'))

        text = self.voice.recognize(converted)
        update.message_text = text
        logger.debug(f"Voice message received: {text}")

        self.text_update_received(bot, update)

    def text_update_received(self, bot: IBotAPIClient, update: Update):
        self.nlp.insert_understanding(update)
        self._process_update(bot, update)

    def _process_update(self, bot, update):
        context = self.context_manager.add_incoming_update(update)
        next_response = self.planning_agent.build_next_actions(context)

        actions = next_response.collect_actions()

        if self.recorder:
            self.recorder.record_dialog(update, actions)

        bot.perform_action(actions)
        context.add_actions(actions)

        update.save()
