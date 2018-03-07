import json
import os
from difflib import SequenceMatcher
from pprint import pprint
from typing import List

PATH = os.path.dirname(os.path.realpath(__file__))


def similarity(user_input, compare_to) -> float:
    compare_to = compare_to.lower()
    user_input = user_input.lower()

    add = 0
    if user_input in compare_to:
        add = 0.15

    return min(1,
               SequenceMatcher(None, user_input, compare_to).ratio() + add)


def load_devices():
    devices_dict = json.load(open('{}/phonedata/devices-latest.json'.format(PATH), 'r'))
    results = list()

    for k, v in devices_dict.items():
        if any(x['name'] == v['name']['id'] for x in results):
            # remove duplicates
            continue
        results.append({
            'id': k,
            'maker': v['maker']['name'],
            'name': v['name']['id']
        })
    return results


def open_image(device_id):
    path = os.path.join(PATH, 'phonedata', 'photo', device_id)
    return open(path, 'rb')


def devices_by_name(name: str) -> List[str]:
    matches = list()
    for d in DEVICES:
        formatted = format_device(d).lower()
        if name.lower() == formatted.lower():
            return [d]
        sim = similarity(name, formatted)
        if sim > 0.3:
            matches.append((d, sim))
    return sorted(matches, key=lambda x: x[1], reverse=True)[:15]


def format_device(device):
    return device['maker'] + ' ' + device['name']


DEVICES = load_devices()

if __name__ == '__main__':
    identifier = 'huawei'
    print()
    result = devices_by_name(identifier)
    pprint(result)
    print()
    pprint([(format_device(x[0]), x[1]) for x in devices_by_name(identifier)])
