from model import *

Update.drop_table(fail_silently=True, cascade=True)
Update.create_table()
UserAnswers.drop_table(fail_silently=True, cascade=True)
UserAnswers.create_table()
User.drop_table(fail_silently=True, cascade=True)
User.create_table()
