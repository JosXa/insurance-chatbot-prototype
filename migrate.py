from model import *


def reset_answers():
    UserAnswers.drop_table(fail_silently=True, cascade=True)
    UserAnswers.create_table()
    print("Reset all answers")


def reset_all():
    Update.drop_table(fail_silently=True, cascade=True)
    Update.create_table()
    User.drop_table(fail_silently=True, cascade=True)
    User.create_table()
    reset_answers()
