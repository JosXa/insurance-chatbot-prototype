import os
import yaml


def load_yaml_as_dict(filepath: str) -> dict:
    with open(filepath) as handle:
        return yaml.load(handle)


