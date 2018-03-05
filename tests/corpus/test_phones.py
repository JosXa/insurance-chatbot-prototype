from pprint import pprint

import pytest
from corpus.phones import devices_by_name, format_device


def test_devices_by_name():
    cases = {
        'iphone 6s': 'iPhone 6s Plus',
        'samsung s3': 'Galaxy S III',
        'nexus 6p': 'Nexus 6P'
    }

    for name, expected in cases.items():
        results = [x[0]['name'] for x in devices_by_name(name)[:10]]
        assert expected in results, \
            f'{expected} not in top ten results: {results}'
