import json
import os
import pathlib

from decouple import config

LIVE_DEMO_MODE = config('DEMO_MODE', cast=bool, default=False)
PORT = config('PORT', cast=int, default=5000)
APP_URL = 'https://bachelor-thesis.herokuapp.com/'
DEBUG_MODE = config('DEBUG', cast=bool, default=False)
NO_DELAYS = config('NO_DELAYS', cast=bool, default=False)

REDIS_URL = config('REDIS_URL')
DIALOGFLOW_ACCESS_TOKEN = config('DIALOGFLOW_ACCESS_TOKEN')
FACEBOOK_ACCESS_TOKEN = config('FACEBOOK_ACCESS_TOKEN')
TELEGRAM_ACCESS_TOKEN = config('TELEGRAM_ACCESS_TOKEN')
TWILIO_ACCESS_TOKEN = config('TWILIO_ACCESS_TOKEN')
TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID')
DATABASE_URL = config('DATABASE_URL')
ENABLE_CONVERSATION_RECORDING = config('RECORD_CONVERSATIONS', cast=bool, default=True)
CONTEXT_LOOKUP_RECENCY = 15
SUPPORT_CHANNEL_ID = -1001265422831
GOOGLE_SERVICE_ACCOUNT_KEY = config('GOOGLE_SERVICE_ACCOUNT_KEY').replace("\\n", "\n")
# Insert google private key into a template of the json configuration and add it to environment vars
_root_dir = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists('tmp'):
    os.makedirs('tmp')
google_service_account_file = _root_dir / 'tmp' / 'service-account-file.json'
template = json.load(open(_root_dir / "google-service-template.json", 'r'))
template["private_key"] = GOOGLE_SERVICE_ACCOUNT_KEY
json.dump(template, open(google_service_account_file, 'w+'))
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(google_service_account_file)

# Whether to remove the ForceReply markup in Telegram for any non-keyboard message (useful for demo)
ALWAYS_REMOVE_MARKUP = LIVE_DEMO_MODE
