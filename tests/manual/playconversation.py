import unittest
import random

import time

import os

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

    def _get_latest_recording(self):
        path = '/home/joscha/bachelorarbeit/src/tests/recordings/valid'
        files = os.listdir(path)
        print(files[-1])
        return os.path.join(path, files[-1])

    def test_play_recording(self):
        self.live_mode = False

        rec = utils.load_yaml_as_dict(self._get_latest_recording())
        for r in rec:
            text = r['user_says']
            print(f'User says: {text}...', end=' ', flush=True)
            response = self.send_message_get_response(text)
            print(f'Bot says: {response.text}')
            time.sleep(random.random() * 1.8)


if __name__ == '__main__':
    unittest.main()
