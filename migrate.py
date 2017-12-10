from model import *

User.drop_table(fail_silently=True)
User.create_table()
