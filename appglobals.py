import os
import pathlib

from playhouse.db_url import connect

import settings

_db = None
ROOT_DIR = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = ROOT_DIR / 'model' / 'data'


def db():
    global _db
    if not _db:
        _db = connect(settings.DATABASE_URL, autorollback=True)
    return _db


# globals
db = db()
