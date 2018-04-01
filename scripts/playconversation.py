import os
import random
import time

import settings
import util
from scripts.visualize import visualize_recording
from tests.integration.integrationtestbase import IntegrationTestBase


class FullConversationIntegrationTests(IntegrationTestBase):

    def _get_latest_recording(self, index=0):
        path = os.path.join(RECORDING_PATH, 'valid')
        files = os.listdir(path)
        idx = - (index + 1)
        print(files[idx])
        return os.path.join(path, files[idx])

    def play_recording(self, index=0, natural=False):
        print("Sending /reset to restart and reset the bot")
        self.client.send_message(self._peer, message="/reset")
        self.delete_history()
        time.sleep(3)

        filepath = self._get_latest_recording(index)
        rec = util.load_yaml_as_dict(filepath)
        try:
            for r in rec:
                text = r['user_says']
                if not text or text in ("", " "):
                    continue
                if natural and settings.NO_DELAYS:
                    sl = random.randint(10, 30) / 10
                    print(f"Sleeping for {sl}")
                    time.sleep(sl)
                print(f'User says: "{text}"...', end=' ', flush=True)
                response = self.send_message_get_response(text)
                print(f'Bot answers: {response.text}')
        finally:
            self.disconnect()
        return filepath


if __name__ == '__main__':
    c = FullConversationIntegrationTests()
    c.live_mode = False
    c.play_recording(index=0, natural=True)
