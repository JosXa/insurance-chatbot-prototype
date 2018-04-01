""" These are matching functions, named after question titles and are called through a getattr() expression when the
user utters a response to a question. """
import re
import traceback
from collections import namedtuple
from pprint import pprint

import dateparser
import regex

from corpus import phones
from corpus.phones import format_device
from logic.sentencecomposer import SentenceComposer


def model_identifier(r: SentenceComposer, c, q):
    answer = c.last_user_utterance.text
    results = phones.devices_by_name(answer)
    choices = [format_device(x[0]) for x in results]
    if not results:
        r.say('no phone results')
        return None
    if len(results) == 1:
        device_id = results[0][0]['id']
        r.send_media(device_id)
        return choices[0]
    return choices


def date_and_time(r, c, q):
    answer = c.last_user_utterance.text

    try:
        result = dateparser.parse(answer, languages=['de'])
        if result:
            return result

        # Perform some very naive transformations to try get the string to parse
        answer = re.sub(r'(um|bis|am)', "", answer, re.IGNORECASE)
        result = dateparser.parse(answer, languages=['de'])
        if result:
            return result

        answer = re.sub(r'[a-zA-ZöäüÖÄÜ]', "", answer)
        result = dateparser.parse(answer, languages=['de'])
        if result:
            return result

        return False
    except:
        traceback.print_exc()
        return False


FirstLastName = namedtuple("FirstLastName", ["first_name", "last_name"])


def _parse_names(text) -> FirstLastName:
    # https://stackoverflow.com/questions/44460642/python-regex-duplicate-names-in-named-groups
    match = regex.match(r'^(?|'
                        r'(?P<last_name>(?:\s?\S+){1,3}), (?P<first_name>\w+)'
                        r'|(?P<first_name>\w+) (?P<last_name>(?:\s?\S+){1,3})'
                        r')$', text, regex.MULTILINE)

    if not match:
        return None

    names = match.groupdict()
    last_name_parts = names['last_name'].strip().split()

    if len(last_name_parts) == 1:
        last_name = last_name_parts[0].title()
    else:
        # Uppercase last word of the last name
        last_name = ' '.join(last_name_parts[:-1]) + ' ' + last_name_parts[-1].title()

    return FirstLastName(
        first_name=names['first_name'].strip().title(),
        last_name=last_name
    )


def name(r, c, question):
    answer = c.last_user_utterance.text

    names = _parse_names(answer)

    if names is None:
        r.say('sorry', 'invalid answer').give_hint(question)
        return

    c.user.first_name = names.first_name
    c.user.last_name = names.last_name

    # We implicitly ground the user's first_name here
    r.say("ok thank you ground name")

    c.add_answer_to_question(question, f"{names.first_name}, {names.last_name}")

    from logic.rules.claimhandlers import ask_next_question
    ask_next_question(r, c)
    return None


def cause_of_damage(r, c, question):
    answer = c.last_user_utterance.text

    words = answer.split()

    if len(words) < 20:
        r.say("too short damage cause", parameters=dict(words_required=20))
        return None
    return answer
