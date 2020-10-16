# Plex-Bot

Plex-bot is application to query and queue movies for my Plex server directly from a discord chat.

## Description

Members of the chat can submit requests using the discord bot which will make requests to a IMDB API and try to match the members search. The bot features a chat function that allows users to interact and help it learn new conversational responses.

## Installing
 Clone the repo 
```bash
 git clone https://github.com/gitpalacio/plex-bot.git
```

 Install dependencies
```bash
pip install -r requirements.txt
```
Create a environment file to store your variables for AWS (assuming your account is setup),
Discord Token, and Rapid API key for IMDB.
```bash
touch plex-bot/plex-request/.env
```
```bash
DISCORD_TOKEN={token}
DISCORD_GUILD=PALAC+
AWS_ACCESS_KEY={access_key}
AWS_SECRET_KEY={secret_key}
AWS_REGION=us-west-2
RAPID_API_URL={url}
RAPID_API_HOST={host}
RAPID_API_KEY={api_key}
```

## Usage
- To activate the bot
```bash
python plex-bot/plex-request/bot.py
```
- To submit a request, use the +request command in discord chat.
(+request movie land before time)


## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
