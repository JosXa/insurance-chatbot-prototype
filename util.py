import itertools

from ruamel.yaml import YAML, ruamel

yaml = YAML(typ='safe')


def load_yaml_as_dict(filepath: str) -> dict:
    with open(filepath) as handle:
        return yaml.load(handle)


def save_dict_as_yaml(filepath, values):
    with open(filepath, 'w') as handle:
        ruamel.yaml.round_trip_dump(values, handle, default_flow_style=False, explicit_start=True)


from functools import wraps
from time import time


def mutually_exclusive(values):
    try:
        return sorted(list(values)).index(True) == len(values) - 1
    except ValueError:
        return True


def build_menu(buttons,
               n_cols,
               header_buttons=None,
               footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        print('func:%r args:[%r, %r] took: %2.4f sec' % \
              (f.__name__, args, kw, te - ts))
        return result

    return wrap


def paginate(iterable, page_size):
    while True:
        i1, i2 = itertools.tee(iterable)
        iterable, page = (itertools.islice(i1, page_size, None),
                          list(itertools.islice(i2, page_size)))
        if len(page) == 0:
            break
        yield page


def calculate_natural_delay(message_text: str):
    from core import ChatAction
    msg_len = len(message_text)
    human_delay = min(ChatAction.Delay.VERY_LONG.value, (msg_len * 0.03 + 0.35))
    return human_delay
