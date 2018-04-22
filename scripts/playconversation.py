import os
import random
import time

import settings
import util
from tests.integration.integrationtestbase import IntegrationTestBase

RECORDING_PATH = 'valid-recordings'


class FullConversationIntegrationTests(IntegrationTestBase):

    def _get_latest_recording(self, index=0):
        files = os.listdir(RECORDING_PATH)
        idx = - (index + 1)
        print(files[idx])
        return os.path.join(RECORDING_PATH, files[idx])

    def play_recording(self, index=0):
        print("Sending /reset to restart and reset the bot")
        self.send_message_get_response("/reset", timeout=7, raise_=False)
        self.delete_history()

        recording_file = self._get_latest_recording(index)
        rec = util.load_yaml_as_dict(recording_file)

        try:
            was_force_reply = False
            response = None
            for r in rec:
                text = r['user_says']
                if not text or text in ("", " "):
                    continue

                print(f'User says: "{text}"...', end=' ', flush=True)
                reply_to = response.message_id if was_force_reply else None

                time.sleep(util.calculate_natural_delay(text) + util.calculate_natural_delay(response.text) if
                           response else 0.5)

                response = self.send_message_get_response(text, reply_to=reply_to)

                was_force_reply = response.is_force_reply
                print(f'Bot answers: {response.text}')
        finally:
            self.disconnect()
        return recording_file


if __name__ == '__main__':
    c = FullConversationIntegrationTests()
    c.live_mode = True
    c.play_recording(index=0)
