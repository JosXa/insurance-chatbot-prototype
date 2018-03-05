import unittest

from core.controller import IntentHandler


class MyTestCase(unittest.TestCase):
    def test_matches(self):
        def dummy():
            pass

        handler = IntentHandler(dummy, 'start', None)
        self.assertTrue(handler.matches('start', {}))
        self.assertTrue(handler.matches('start', {'kek': 'kektarine'}))
        self.assertFalse(handler.matches(None, {}))
        self.assertFalse(handler.matches('kek', {}))
        self.assertFalse(handler.matches(None, {'kek': 'kektarine'}))

        handler = IntentHandler(dummy, None, ['param'])
        self.assertTrue(handler.matches('something', {'param': True}))
        self.assertTrue(handler.matches('somethingelse', {'param': True}))
        self.assertFalse(handler.matches(None, {}))
        self.assertFalse(handler.matches('kek', {}))

        handler = IntentHandler(dummy, ['t1', 't2'], None)
        self.assertTrue(handler.matches('t1', {'param': True}))
        self.assertTrue(handler.matches('t1', {}))
        self.assertTrue(handler.matches('t2', {'param': True}))
        self.assertTrue(handler.matches('t2', {}))
        self.assertFalse(handler.matches('t3', {}))
        self.assertFalse(handler.matches('t3', {'param': True}))
        self.assertFalse(handler.matches(None, {}))
        self.assertFalse(handler.matches('kek', {}))

        handler = IntentHandler(dummy, None, 'formal_address')
        self.assertFalse(handler.matches('start', None))

        handler = IntentHandler(dummy, None, ['p1', 'p2'])
        self.assertTrue(handler.matches('start', {'p1': 'kek', 'p2': 'kektarine'}))
        self.assertTrue(handler.matches(None, {'p1': 'kek', 'p2': 'kektarine'}))
        self.assertTrue(handler.matches('start', {'p1': 'kek', 'p2': 'kektarine', 'p3': 'test'}))
        self.assertFalse(handler.matches(None, {'p1': 'kek', 'p3': 'test'}))
        self.assertFalse(handler.matches('start', {'p1': 'kek', 'p3': 'test'}))
        self.assertFalse(handler.matches(None, {'p3': 'kek'}))
        self.assertFalse(handler.matches('start', {'p3': 'kek'}))

        handler = IntentHandler(dummy, 't1', ['p1', 'p2'])
        self.assertTrue(handler.matches('t1', {'p1': 'kek', 'p2': 'kektarine'}))
        self.assertFalse(handler.matches('kek', {'p1': 'kek', 'p2': 'kektarine'}))


if __name__ == '__main__':
    unittest.main()

