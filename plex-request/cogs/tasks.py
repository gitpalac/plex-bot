import discord
from discord.ext import commands, tasks
from aws import Notification, Queue
import sys
import json
# sys.path.insert(0, "/home/localadmin/private/scripts/torrent-pirate")
sys.path.insert(0, '/Users/mikepalacio/dev/torrent-pirate')
from parrotbay import parrot


class Task(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.download_queue = []
        self.batch_download.start()
        print('polling download queue...')
        self.check_dl_status.start()

    @tasks.loop(minutes=60)
    async def batch_download(self):
        await self.bot.wait_until_ready()
        print('starting content update...')
        queue = Queue('plex_queue')
        messages = queue.get_messages()
        for msg in messages:
            msg = json.loads(msg['Body'])
            msg = json.loads(msg['Records'][0]['Sns']['Message'])
            print(f"Searching for {msg['title'] + ' ' + str(msg['year'])}")
            pirate = parrot.PirateClient()
            pirate.search(msg['title'] + ' ' + str(msg['year']))
            torrent = pirate.best_match()
            torrent['imdb_title'] = msg['title']
            torrent['image_url'] = msg['image_url']
            torrent['year'] = msg['year']
            tor = parrot.TorrentClient()
            tor.set_savepath('/Users/mikepalacio/Desktop')
            tor.download(torrent)
            self.download_queue.append(torrent)

    @tasks.loop(minutes=5)
    async def check_dl_status(self):
        await self.bot.wait_until_ready()
        tor = parrot.TorrentClient()
        for torrent in tor.torrents:
            for download in self.download_queue:
                dl_magnet = download['magnet'].split('&')[0].lower()
                to_magnet = torrent['magnet_uri'].split('&')[0].lower()
                if dl_magnet == to_magnet:
                    print(f"{torrent['name']} was downloaded successfully")
                    self.download_queue.remove(download)
                    channel = self.bot.get_channel(727546317970341969)  ##UPDATES
                    embed = discord.Embed(title=download['imdb_title'],
                                          colour=discord.Colour.teal())
                    embed.set_image(url=download['image_url'])
                    embed.set_author(name="Just Added",
                                     icon_url="https://www.plex.tv/wp-content/uploads/2018/01/pmp-icon-1.png")
                    await channel.send(embed=embed)


def setup(client):
    client.add_cog(Task(client))