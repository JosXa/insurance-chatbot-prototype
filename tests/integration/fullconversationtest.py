import unittest

from tests.integration.integrationtestbase import IntegrationTestBase


class MyTestCase(IntegrationTestBase):
    def test_full_conversation(self):
        hallo = self.send_message_get_response("Hallo")
        print(hallo.text)


if __name__ == '__main__':
    unittest.main()
