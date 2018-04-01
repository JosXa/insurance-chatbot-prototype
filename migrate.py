from pprint import pprint
from typing import List

from decouple import config
from redis import StrictRedis
from redis_collections import Dict

import settings
from model import *


def reset_answers(users: List[User] = None):
    if users is None:
        UserAnswers.drop_table()
        UserAnswers.create_table()
    else:
        UserAnswers.delete().where(UserAnswers.user << users).execute()


def clear_redis(users: List[User] = None):
    conn = StrictRedis.from_url(settings.REDIS_URL)
    if users:
        to_delete = []
        for u in users:
            to_delete.extend(conn.keys(rf'{u.id}*'))
        for k in to_delete:
            conn.delete(k)
    else:
        conn.flushdb()


def reset_all():
    Update.drop_table(fail_silently=True, cascade=True)
    Update.create_table()
    User.drop_table(fail_silently=True, cascade=True)
    User.create_table()
    # User.insert(telegram_id=62056065, formal_address=False).execute()
    Update.drop_table(fail_silently=True, cascade=True)
    Update.create_table()
    reset_answers()
    clear_redis()


if __name__ == '__main__':
    # reset_all()
    clear_redis()
