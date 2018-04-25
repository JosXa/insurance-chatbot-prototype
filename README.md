## Local Installation

1. `git clone https://github.com/JosXa/bachelor-thesis-insurance`
2. Install requirements: `pip install -r requirements.txt`
3. Create new Bot on Telegram by sending the command /newbot to @BotFather and follow the instru
4. Copy .env settings file to root directory, add Bot Token where applicable
5. Run `bot.py` under python3.6 or higher

## Deployment

1. On Heroku: Under resources make sure instance is running as "web" service
2. Redis und PostgreSQL als Heroku Addons installieren
3. ggf. lokal den toolbelt installieren


## TODO
- Dialogflow STT nutzen statt eigener Konvertierung mit ffmpeg und Google SR
- MIT Lizenz open source
