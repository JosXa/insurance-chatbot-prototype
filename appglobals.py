import os

from playhouse.db_url import connect

import settings

_db = None
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


def db():
    global _db
    if not _db:
        _db = connect(settings.DATABASE_URI)
    return _db


def disconnect():
    # global _db
    # _db.close()
    pass  # I assume this is done by peewee automatically upon receiving a signal


# globals
db = db()

