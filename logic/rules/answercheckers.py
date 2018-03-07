""" These are matching functions, named after question titles and are called through a getattr() expression when the
user utters a response to a question. """
from corpus import phones
from corpus.phones import format_device


def model_identifier(r, c):
    answer = c.last_user_utterance.text
    choices = [format_device(x[0]) for x in phones.devices_by_name(answer)]
    if not choices:
        r.say('no phone results')
    if len(choices) == 1:
        from logic.rules.claimhandlers import store_answer
        return store_answer(r, c, choices[0])
    else:
        r.ask('please select choice', choices=choices)
