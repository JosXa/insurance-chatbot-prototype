import random

import time

import os

from telethon import events, TelegramClient

import utils
from tests.integration.integrationtestbase import IntegrationTestBase


class FullConversationIntegrationTests(IntegrationTestBase):

    # def test_full_conversation(self):
    #     hallo = self.send_message_get_response("Hallo")
    #     self.assertRegex(hallo.text, r'^(Guten Tag|Hallo).*')
    #
    #     hmm = self.send_message_get_response("Hmm")
    #     self.assertRegex(hmm.text, r'.*Ich kann.*')
    #
    #     ja_gern = self.send_message_get_response("Ja, gern")
    #     self.assertRegex(ja_gern.text, r'.*Versicherungsschein.*')

    def _get_latest_recording(self, index=0):
        path = '/home/joscha/bachelorarbeit/src/tests_manual/recordings/valid'
        files = os.listdir(path)
        idx = - (index + 1)
        print(files[idx])
        return os.path.join(path, files[idx])

    def play_recording(self, index=0):
        self.live_mode = False
        print("Sending /r to restart the bot")
        self.client.send_message(entity=self._peer, message="/r")
        time.sleep(2.5)

        rec = utils.load_yaml_as_dict(self._get_latest_recording(index))
        try:
            for r in rec:
                text = r['user_says']
                if not text or text in ("", " "):
                    continue
                print(f'User says: "{text}"...', end=' ', flush=True)
                response = self.send_message_get_response(text)
                print(f'Bot answers: {response.text}')
        finally:
            self.disconnect()


if __name__ == '__main__':
    c = FullConversationIntegrationTests()
    c.play_recording(index=0)
