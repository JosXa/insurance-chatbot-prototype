from datetime import datetime as dtime, timedelta as tdelta

import pytest

from core import Context, MessageUnderstanding
from corpus.responsetemplates import SelectiveTemplateLoader, TemplateRenderer
from logic.rules import answercheckers as ans
from logic.sentencecomposer import SentenceComposer
from model import User


def test__parse_name():
    n = "jan Van der linden"
    res = ans._parse_names(n)
    assert res.first_name == "Jan"
    assert res.last_name == "Van der Linden"

    n = "van der linden, Jan"
    res = ans._parse_names(n)
    assert res.first_name == "Jan"
    assert res.last_name == "van der Linden"

    n = "max mustermann"
    res = ans._parse_names(n)
    assert res.first_name == "Max"
    assert res.last_name == "Mustermann"

    n = "mustermann, max"
    res = ans._parse_names(n)
    assert res.first_name == "Max"
    assert res.last_name == "Mustermann"

    assert ans._parse_names("was meinst du damit genau?") is None


@pytest.fixture()
def user():
    return User()


@pytest.fixture()
def c():
    return Context(None, None)


@pytest.fixture()
def r(user):
    return SentenceComposer(user,
                            template_loader=SelectiveTemplateLoader(),
                            template_renderer=TemplateRenderer({}))


@pytest.fixture()
def message(c):
    """ Adds a message to context and returns the context """

    def insert_understanding(text):
        u = MessageUnderstanding(text, "test")
        c.add_user_utterance(u)
        return c

    return insert_understanding


def test_date_and_time(message):
    now = dtime.now()

    def roughly_equals(d1, d2):
        return abs(d2 - d1) <= tdelta(minutes=10)

    def parse_date(text):
        return ans.date_and_time(r, message(text), None)

    assert parse_date("Test") is False
    assert parse_date("32.01.2010") is False
    assert roughly_equals(parse_date("vor einer woche") + tdelta(weeks=1), now)
    assert roughly_equals(parse_date("10.01.2017 15:30"), dtime(2017, 1, 10, 15, 30))
    assert roughly_equals(parse_date("10.3.2018 15:30"), dtime(2018, 3, 10, 15, 30))
    assert roughly_equals(parse_date("10.01.2017"), dtime(2017, 1, 10))
    assert roughly_equals(parse_date("22. Januar 13:30"), dtime(now.year, 1, 22, 13, 30))

    tmr = now + tdelta(days=1)
    assert roughly_equals(parse_date("morgen um 13:45"), dtime(tmr.year, tmr.month, tmr.day, 13, 45))
