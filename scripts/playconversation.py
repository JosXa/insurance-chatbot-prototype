import os
import time

import settings
import util
from tests.integration.integrationtestbase import IntegrationTestBase

RECORDING_PATH = 'valid-recordings'


class FullConversationIntegrationTests(IntegrationTestBase):

    @staticmethod
    def _get_latest_recording(index=0):
        files = os.listdir(RECORDING_PATH)
        idx = - (index + 1)
        print(files[idx])
        return os.path.join(RECORDING_PATH, files[idx])

    def wait_user_send(self, next_message, reply_to=None):
        self.set_draft(next_message, reply_to=reply_to)

        return self.wait_outgoing(next_message)

    @util.timing
    def play_recording(self, index=0):
        recording_file = self._get_latest_recording(index)
        rec = util.load_yaml_as_dict(recording_file)

        self.set_draft("", reply_to=None)
        print("Sending /reset to reset the bot")
        self.send_message_get_response("/reset", timeout=20, raise_=False, min_wait_consecutive=0)
        time.sleep(2.2)
        self.delete_history()

        self.wait_user_send("/start")

        try:
            was_force_reply = False
            response = None
            for r in rec:
                text = r['user_says']
                if not text or text in ("", " ", "/start"):
                    continue

                reply_to = response.message_id if was_force_reply else None

                print(f'User says: "{text}"...', end=' ', flush=True)

                if r.get('auto', True):
                    delay = util.calculate_natural_delay(text) + util.calculate_natural_delay(
                        response.text) if response else 0.5
                    if settings.LIVE_DEMO_MODE:
                        delay += 0.8  # make sure we don't interrupt the bot
                    delay = min(delay, 5)
                    time.sleep(delay)
                    response = self.send_message_get_response(text, reply_to=reply_to)
                else:
                    response = self.wait_user_send(text, reply_to)
                print('sent.')

                was_force_reply = response.is_force_reply

                print(f'Bot answers: "{response.text}"')

        finally:
            self.disconnect()
        return recording_file


if __name__ == '__main__':
    c = FullConversationIntegrationTests()
    c.live_mode = True
    c.play_recording(index=0)
