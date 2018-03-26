import unittest

from core import MessageUnderstanding
from core.routing import IntentHandler


def dummy():
    pass


def u(intent, parameters):
    return MessageUnderstanding(intent=intent, parameters=parameters, text="")


def test_intent_handler():
    handler = IntentHandler(dummy, intents='start', parameters=None)
    assert handler.matches(u('start', {}))
    assert handler.matches(u('start', {'kek': 'kektarine'}))
    assert not handler.matches(u(None, {}))
    assert not handler.matches(u('kek', {}))
    assert not handler.matches(u(None, {'kek': 'kektarine'}))

    handler = IntentHandler(dummy, None, ['param'])
    assert handler.matches(u('something', {'param': True}))
    assert handler.matches(u('somethingelse', {'param': True}))
    assert handler.matches(u(None, {}))
    assert handler.matches(u('kek', {}))

    handler = IntentHandler(dummy, intents=['t1', 't2'], parameters=None)
    assert handler.matches(u('t1', {'param': True}))
    assert handler.matches(u('t1', {}))
    assert handler.matches(u('t2', {'param': True}))
    assert handler.matches(u('t2', {}))
    assert handler.matches(u('t3', {}))
    assert handler.matches(u('t3', {'param': True}))
    assert handler.matches(u(None, {}))
    assert handler.matches(u('kek', {}))

    handler = IntentHandler(dummy, intents=None, parameters='formal_address')
    assert handler.matches(u('start', None))

    handler = IntentHandler(dummy, intents=None, parameters=['p1', 'p2'])
    assert handler.matches(u('start', {'p1': 'kek', 'p2': 'kektarine'}))
    assert handler.matches(u(None, {'p1': 'kek', 'p2': 'kektarine'}))
    assert handler.matches(u('start', {'p1': 'kek', 'p2': 'kektarine', 'p3': 'test'}))
    assert handler.matches(u(None, {'p1': 'kek', 'p3': 'test'}))
    assert handler.matches(u('start', {'p1': 'kek', 'p3': 'test'}))
    assert handler.matches(u(None, {'p3': 'kek'}))
    assert handler.matches(u('start', {'p3': 'kek'}))

    handler = IntentHandler(dummy, 't1', ['p1', 'p2'])
    assert handler.matches(u('t1', {'p1': 'kek', 'p2': 'kektarine'}))
    assert handler.matches(u('kek', {'p1': 'kek', 'p2': 'kektarine'}))
