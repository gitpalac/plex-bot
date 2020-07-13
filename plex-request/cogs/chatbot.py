from chatterbot import ChatBot, comparisons, response_selection
from chatterbot.trainers import ListTrainer
from chatterbot.conversation import Statement
import discord
from discord.ext import commands
import logging
import json
import csv
import os
from dotenv import load_dotenv
import argparse


class Chat(commands.Cog):

    def __init__(self, client):
        parser = argparse.ArgumentParser()
        parser.add_argument('-m', help='run dev enviroment')
        prefix = ''
        args = parser.parse_args()
        if args.m:
            if args.m == 'dev':
                prefix = 'DEV_'
        load_dotenv()
        working_dir = os.getenv(prefix + 'WORKING_DIR')
        data_dir = os.path.join(working_dir, 'plex-request/data')
        self.bot = client
        self.chatbot = ChatBot('PalacBot',
                               storage_adapter='chatterbot.storage.SQLStorageAdapter',
                               logic_adapters=[{
                                   'import_path': 'chatterbot.logic.BestMatch',
                                   'response_selection_method' :
                                       response_selection.get_most_frequent_response,
                                   'default_response': 'I am sorry, but I do not understand.',
                                   'maximum_similarity_threshold': 0.93}])

        self.trainer = ListTrainer(self.chatbot)
        print('Training ChatBot...')
        for filename in os.listdir(data_dir):
            if filename.endswith('.json'):
                print(f'Loading this file: {filename}')
                with open(os.path.join(data_dir, filename)) as jsonf:
                    data = json.load(jsonf)
                    self.trainer.train([msg['content'] for msg in data['messages']
                                        if msg['type'] == 'Default' and len(msg['content']) > 0
                                        and msg['content'].find('https://') == -1]
                                       )

            elif filename.endswith('.csv'):
                print(f'Loading this file: {filename}')
                training = []
                with open(os.path.join(data_dir, filename)) as csvf:
                    csvreader = csv.reader(csvf, delimiter=',')
                    for row in csvreader:
                        training.append(row[0])
                self.trainer.train(training)

    @commands.Cog.listener()
    async def on_message(self, message):
        botuser = self.bot.user
        if message.author != botuser:
            ctx = await self.bot.get_context(message)
            if not ctx.valid:
                if botuser.mentioned_in(message):
                    message_content = None
                    for usr in message.mentions:
                        message_content = message.content.replace(f'<@!{usr.id}>','').replace(f'<@{usr.id}', '').strip()
                    print(f"Message Recieved: {message_content}")
                    await message.channel.send(self.chatbot.get_response(message_content))

                elif message.type == discord.MessageType.default:
                    messages = await message.channel.history(limit=2).flatten()
                    previous_message = messages[1]
                    if previous_message.author != botuser:
                        user_input = Statement(text=previous_message.content)
                        user_response = Statement(text=message.content)
                        self.chatbot.learn_response(user_response, user_input)
                        print(f"{botuser.name} Learned New Response '{user_response.text}' as a response to '{user_input.text}'")
                    else:
                        pass
                else:
                    pass
            else:
                pass

def setup(client):
    client.add_cog(Chat(client))