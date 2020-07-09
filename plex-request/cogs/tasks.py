import discord
from discord.ext import commands, tasks
from aws import Notification, Queue
import sys
import json
import logging
import unicodedata

try:
    sys.path.insert(0, "/home/localadmin/private/scripts/torrent-pirate")
except Exception as e:
    print(e)
finally: sys.path.insert(0, '/Users/mikepalacio/dev/torrent-pirate')

from parrotbay import parrot

save_path = '/home/localadmin/public/movies'


class Task(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.download_queue = []
        self.batch_download.start()
        self.check_dl_status.start()

    @tasks.loop(minutes=60)
    async def batch_download(self):
        await self.bot.wait_until_ready()
        print('downloading from queue...')
        queue = Queue('plex_queue')
        messages = queue.get_messages()
        for msg in messages:
            try:
                msg = json.loads(msg['Body'])
                msg = json.loads(msg['Records'][0]['Sns']['Message'], encoding='utf-8')
                title = unicodedata.normalize('NFD', msg['title']).encode('ascii', 'ignore').decode("utf-8")
                print(f"Searching for {title + ' ' + str(msg['year'])}")
                pirate = parrot.PirateClient()
                pirate.search(title + ' ' + str(msg['year']))
                try:
                    torrent = pirate.best_match()
                except IndexError:
                    keywords =  unicodedata.normalize('NFD',
                                                      (' '.join(msg['keywords']))
                                                      .encode('ascii', 'ignore')
                                                      .decode("utf-8"))
                    pirate.search(keywords + ' ' + str(msg['year']))
                    torrent = pirate.best_match()
                torrent['imdb_title'] = msg['title']
                torrent['image_url'] = msg['image_url']
                torrent['year'] = msg['year']
                tor = parrot.TorrentClient()
                tor.set_savepath(save_path)
                tor.download(torrent)
                self.download_queue.append(torrent)
            except Exception as e:
                if isinstance(e, IndexError):
                    reason = 'no valid download links were found.'
                elif isinstance(e, parrot.SpaceLimitError):
                    reason = e
                else:
                    reason = 'of an unknown error.'
                requestor = self.bot.get_user(msg['created_by'])
                await self.bot.get_channel(727546317970341969) \
                    .send(f"""Sorry {requestor.mention}, but I was not able to download the title "{msg['title']}" because {reason}.. 😢""")
                print(f'Issue downloading {title} from queue --{e}')
                continue


    @tasks.loop(minutes=20)
    async def check_dl_status(self):
        print('checking for completed downloads...', flush=True)
        await self.bot.wait_until_ready()
        try:
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
        except Exception as e:
            print(f'Issue checking DL status --{e}')


def setup(client):
    client.add_cog(Task(client))