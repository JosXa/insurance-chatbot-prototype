import unittest
import random

import time

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

    def test_play_recording(self):
        recording_file = '/home/joscha/bachelorarbeit/src/tests/recordings/1_20180205-232828.yml'
        rec = utils.load_yaml_as_dict(recording_file)
        for r in rec:
            text = r['user_says']
            print(f'Sending {text}...', end=' ', flush=True)
            response = self.send_message_get_response(text)
            print(response.text)
            time.sleep(random.random() * 1.8)


if __name__ == '__main__':
    unittest.main()
