import unittest

from tests.integration.integrationtestbase import IntegrationTestBase


class FullConversationIntegrationTests(IntegrationTestBase):
    def test_full_conversation(self):
        hallo = self.send_message_get_response("Hallo")
        self.assertRegex(hallo.text, r'^(Guten Tag|Hallo).*')

        hmm = self.send_message_get_response("Hmm")
        self.assertRegex(hmm.text, r'.*Ich kann.*')

        ja_gern = self.send_message_get_response("Ja, gern")
        self.assertRegex(ja_gern.text, r'.*Versicherungsschein.*')

if __name__ == '__main__':
    unittest.main()
