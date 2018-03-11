""" These are matching functions, named after question titles and are called through a getattr() expression when the
user utters a response to a question. """
import datetime

from core import Context
from corpus import phones
from corpus.phones import format_device
import dateparser

from logic import const


def model_identifier(r, c):
    answer = c.last_user_utterance.text
    choices = [format_device(x[0]) for x in phones.devices_by_name(answer)]
    if not choices:
        r.say('no phone results')
        return None
    if len(choices) == 1:
        return choices[0]
    return choices


def date_and_time(r, c):
    answer = c.last_user_utterance.text
    answer_date = None
    try:
        answer_date = dateparser.parse(answer, languages='de')
    except:
        pass

    if answer_date:
        return answer_date
    else:
        return False
