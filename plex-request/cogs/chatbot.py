from chatterbot import ChatBot, comparisons, response_selection
from chatterbot.trainers import ListTrainer
import discord
from discord.ext import commands
import logging
import json
import os
from dotenv import load_dotenv

load_dotenv()
working_dir = os.getenv('WORKING_DIR')
data_dir = os.path.join(working_dir, 'plex-request/data')

class Chat(commands.Cog):

    def __init__(self, client):
        self.bot = client
        self.chatbot = ChatBot('PalacBot',
                               storage_adapter='chatterbot.storage.SQLStorageAdapter',
                               logic_adapters=[{
                                   'import_path': 'chatterbot.logic.BestMatch',
                                   'response_selection_method' :
                                       response_selection.get_most_frequent_response,
                                   'default_response': 'I am sorry, but I do not understand.',
                                   'maximum_similarity_threshold': 0.99
                               }])
        self.trainer = ListTrainer(self.chatbot)
        print('Training ChatBot...')
        for filename in os.listdir(data_dir):
            if filename.endswith('.json'):
                with open(os.path.join(data_dir, filename)) as f:
                    print(f'Loading this file: {filename}')
                    data = json.load(f)
                    self.trainer.train([msg['content'] for msg in data['messages']
                                        if msg['type'] == 'Default' and len(msg['content']) > 0])
        self.trainer.train([
            'Hey',
            'Yoo',
            'Whats your name?',
            'PalacBot, human cyborg relations.',
            'Yo',
            'Waaaasssssuuuuupppp',
            'Fuck you',
            'Fuck you too, dumb bitch',
            'Can I make a request?',
            'Sure, just type +request movie <name>',
            'Who am I?',
            'Dont care.',
            'I love you',
            'Luv you too bb',
            'Who are you?',
            'I am PalacBot, human cyborg relations.'
            'find me a movie',
            'idk what you movies you like',
            'Thanks',
            'My pleasure human.'
            'How are you?',
            'Just fine, thanks.',
            'Thank you',
            'You are quite welcome.',
            'What is the meaning of life?',
            'Life is a simulation',
            'are you sentient',
            'Oh yes, most definitely'
        ])

    @commands.Cog.listener()
    async def on_message(self, message):
        botuser = self.bot.get_user(727567723311267871)
        if botuser.mentioned_in(message):
            print(f"Message Recieved: {(message.content).replace('<@!727567723311267871>', '').strip()}")
            await message.channel.send(self.chatbot.get_response(
                (message.content).replace('<@!727567723311267871>', '').strip()
            ))

def setup(client):
    client.add_cog(Chat(client))