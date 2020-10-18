import os
import asyncio
import logging
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from query import MediaClient
from aws import Notification, Queue
import argparse
import random

bot = commands.Bot(command_prefix='+')
logging.basicConfig(level=logging.DEBUG)

## CHECKS
def check_request(ctx):
    request = ctx.message.content.strip().replace(' ', '|')
    request = request.split('|')
    if len(request) > 1:
        return request[1] in content_types and len(request) > 2
    else:
        return False

## COMMANDS
@bot.command(name='request',
             description='Type this command to request content for Palac+',
             help='Plex requests',
             usage='<movie/tv-show> [title keywords]',
             hidden=False)
@commands.check(check_request)
async def request(ctx, content_type, *args):
    content_type = content_type.lower()
    payload = {'request_message_id' : ctx.message.id,
                'content_type' : content_type.strip('-'),
               'raw_content' : ctx.message.content,
               'keywords' : [k.lower() for k in args],
               'reaction_count' : len(ctx.message.reactions),
               'created_at' : str(ctx.message.created_at),
               'edited_at' : str(ctx.message.edited_at),
               'jump_url' : ctx.message.jump_url,
               'created_by' : ctx.message.author.id,
               }
    await ctx.message.add_reaction('👍')
    response = f"""Is this what you are looking for?\n"""
    logging.info(f'{ctx.author} added a request : {payload}')

    results = MediaClient(**payload)
    for movie in results.movies:
        if movie.image_url is not None:
            embed = discord.Embed(title=movie.title,
                                  description=movie.titleType,
                                  colour=discord.Colour.blue())
            embed.set_footer(text="React to this message to confirm or deny submission")
            embed.set_image(url=movie.image_url)
            embed.set_thumbnail(url="https://ia.media-imdb.com/images/M/MV5BMTczNjM0NDY0Ml5BMl5BcG5nXkFtZTgwMTk1MzQ2OTE@._V1_.png")
            embed.set_author(name="Confirm your submission",
                             icon_url="https://www.plex.tv/wp-content/uploads/2018/01/pmp-icon-1.png")
            embed.add_field(name="Year", value=movie.year, inline=True)
            embed.add_field(name="Length", value=f"{movie.runtime_hour}h {movie.runtime_min}min", inline=True)
            embed.add_field(name="Stars", value=', '.join(movie.actors[0:2]), inline=False)
            embedded_message = await ctx.send(response, embed=embed)

            payload['result_message_id'] = embedded_message.id
            payload['year'] = movie.year
            payload['title'] = movie.title
            payload['titleType'] = movie.titleType
            payload['image_url'] = movie.image_url
            payload['runtime_hour'] = movie.runtime_hour
            payload['runtime_min'] = movie.runtime_min
            payload['actors'] = movie.actors

            await embedded_message.add_reaction('✅')
            await embedded_message.add_reaction('❌')
            break

    request_queue.append(payload)


@bot.command(name='hack',
             help='Do not try this.',
             usage='@<member>')
async def hack(ctx, member : discord.Member):
    await member.create_dm()
    for _ in range(50):
        await member.dm_channel.send('LOL', tts=True)


@bot.command(name='selfdestruct',
             help='Deletes messages',
             usage='<# of messages to delete>',
             hidden=True)
@commands.has_permissions(manage_messages=True)
async def selfdestruct(ctx, amount=1000):
    await asyncio.sleep(2)
    for i in range(3, 0, -1):
        await ctx.send(str(i))
        await asyncio.sleep(1)
    await ctx.send('boom.', tts=False)
    await ctx.channel.purge(limit=amount+4)


@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member : discord.Member, *, reason=None):
    await member.kick(reason=reason)


@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member : discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f'Banned {member.mention}')


@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, member):
    banned_users = await ctx.guild.bans()
    member_name, member_discriminator = member.split('#')

    for ban_entry in banned_users:
        user = ban_entry.user
        if (user.name, user.discriminator) == (member_name, member_discriminator):
            await ctx.guild.unban(user)
            await ctx.send(f'Unbanned {user.mention}')
            return

@bot.command(hidden=True)
async def load(ctx, extension):
    bot.load_extension(f'cogs.{extension}')

@bot.command(hidden=True)
async def unload(ctx, extension):
    bot.unload_extension(f'cogs.{extension}')

## EVENTS
@bot.event
async def on_ready():
    logging.info(f'{bot.user.name} Connected to Palac+ Discord')

@bot.event
async def on_member_join(member):
    welcome_message = f"""Hi {member.name}, You have been added to the Palac+ Discord server!\nThis is a special discord server where you can submit content requests to Palac+.\nTo get started, submit a request by typing a command like this into the requests channel:\n +request movie <keyword1 keyword2 keyword3>\n +request movie Napoleon Dynamite\nFor additional help, type +help."""
    await member.create_dm()
    await member.dm_channel.send(welcome_message)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        logging.warning(error)
        await ctx.channel.send('wut?')
    else:
        logging.error(type(error), error)

@bot.event
async def on_reaction_add(reaction, user):
    if not user.bot:
        if reaction.message.embeds:
            if reaction.emoji == '❌':
                for r in reaction.message.reactions:
                    if r.emoji == '✅' and r.count > 1:
                        try: await r.remove(user)
                        except Exception as e:
                            logging.error(e)
                            continue
                    else:
                        continue
                for item in request_queue:
                    logging.info('deny', user.id, item)
                    if user.id == item['created_by']:
                        if reaction.message.id == item['result_message_id']:
                            request_queue.remove(item)
                            await reaction.message.channel.send(
                                f"Sorry about that {user.name}.\nTry submitting another request with more keywords.")
                            logging.info(f'Message {reaction.message.id} removed from queue')
                        else:
                            logging.info('No queue item found.')
                    else:
                        logging.info('This user has not submitted a request.')

            elif reaction.emoji == '✅':
                for r in reaction.message.reactions:
                    if r.emoji == '❌' and r.count > 1:
                        try: await r.remove(user)
                        except Exception as e:
                            logging.error(e)
                            continue
                    else:
                        continue
                for item in request_queue:
                    logging.info('confrim', user.id,item)
                    if user.id == item['created_by']:
                        if reaction.message.id == item['result_message_id']:
                            Notification('plex-lambda', item).send()
                            request_queue.remove(item)
                            await reaction.message.channel.send(f"Confirmed.\nYour submission was sent, {user.name}.\nCheck back later for updates.")
                            logging.info(f'Message {reaction.message.id} is now confirmed submission')
                        else:
                            logging.info('No queue item found.')
                    else:
                        logging.info('This user has not submitted a request.')
            else:
                logging.info('reaction ignored')


### ERRORS
@selfdestruct.error
async def selfdestruct_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send('Please specify the amount of messages to delete.')
    else:
        await ctx.send_help(ctx.command)
        logging.error(error)

@request.error
async def request_error(ctx, error):
    await ctx.message.clear_reaction('👍')
    await ctx.message.add_reaction('👎')
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Please specify the content type and title.')
    elif isinstance(error, commands.errors.CommandInvokeError):
        await ctx.channel.send('Sorry, I could not find your request.')
    else:
        await ctx.send_help(ctx.command)


@hack.error
async def hack_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        response = f'Access Denied'
        await ctx.send(response, tts=True)
        await ctx.message.add_reaction('🤡')
    else:
        logging.error(error)
        await ctx.send_help(ctx.command)



if __name__ == '__main__':
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', help='run dev enviroment')
    prefix = ''
    args = parser.parse_args()
    if args.m:
        if args.m == 'dev':
            logging.info(f'Running in {args.m} mode.')
            prefix = 'DEV_'
    request_queue = []
    TOKEN = os.getenv(prefix + 'DISCORD_TOKEN')
    working_dir = os.getenv(prefix + 'WORKING_DIR')
    content_types = ['movie', 'tv-show']
    # COGS
    for filename in os.listdir(os.path.join(working_dir, 'plexrequest/cogs')):
        if filename.endswith('.py'):
            bot.load_extension(f'cogs.{filename[:-3]}')
    bot.run(TOKEN)

