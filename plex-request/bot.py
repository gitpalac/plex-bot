import os
import asyncio
import discord
import io
import aiohttp
from discord.ext import commands
from dotenv import load_dotenv
from query import MediaClient

request_queue = []

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='+')

content_types = ('movie', 'tv-show')

## CHECKS

def valid_request(ctx):
    return ctx.args[1].lower() in content_types and len(ctx.args[1:]) > 0


## COMMANDS

@bot.command(name='request',
             description='Type this command to request content for Palac+',
             help='Submits a request to Palac+.',
             usage='{movie/tv-show} {title keywords}')
# @commands.check(valid_request)
async def request(ctx, content_type, *args):

    content_type = content_type.lower()
    payload = {'message_id' : ctx.message.id,
                'content_type' : content_type.strip('-'),
               'raw_content' : ctx.message.content,
               'keywords' : [k.lower() for k in args],
               'reaction_count' : len(ctx.message.reactions),
               'created_at' : ctx.message.created_at,
               'edited_at' : ctx.message.edited_at,
               'jump_url' : ctx.message.jump_url
               }
    await ctx.message.add_reaction('👍')
    response = f"""Thanks {ctx.author.display_name}.\nYour {content_type.strip('-')} selection was submitted ✅\n"""
    print(f'{ctx.author} added a request : {payload}')

    results = MediaClient(**payload)
    for movie in results.movies:
        if movie.image_url is not None:
            embed = discord.Embed(title=movie.title,
                                  description=movie.titleType,
                                  colour=discord.Colour.blue())
            embed.set_footer(text="Delete this message to remove it from the queue.")
            embed.set_image(url=movie.image_url)
            embed.set_thumbnail(url="https://ia.media-imdb.com/images/M/MV5BMTczNjM0NDY0Ml5BMl5BcG5nXkFtZTgwMTk1MzQ2OTE@._V1_.png")
            embed.set_author(name="Your submission",
                             icon_url="https://www.plex.tv/wp-content/uploads/2018/01/pmp-icon-1.png")
            embed.add_field(name="Year", value=movie.year, inline=True)
            embed.add_field(name="Length", value=f"{movie.runtime_hour}h {movie.runtime_min}min", inline=True)
            embed.add_field(name="Stars", value=', '.join(movie.actors[0:2]), inline=False)
            await ctx.send(response, embed=embed)
            break

    request_queue.append(payload)


@bot.command(name='hack', help='do not try this.')
async def hack(ctx):
    response = f'Access Denied'
    await ctx.send(response, tts=True)
    await ctx.message.add_reaction('🤡')
    await kick(ctx, ctx.author, reason='Cyber Threat Detected')


@bot.command()
@commands.has_permissions(manage_messages=True)
async def selfdestruct(ctx, amount=1000):
    for i in range(3, 0, -1):
        await ctx.send(str(i))
        await asyncio.sleep(1)
    await ctx.send('boom.', tts=False)
    await ctx.channel.purge(limit=amount+4)


@bot.command()
async def kick(ctx, member : discord.Member, *, reason=None):
    await member.kick(reason=reason)


@bot.command()
async def ban(ctx, member : discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f'Banned {member.mention}')


@bot.command()
async def unban(ctx, *, member):
    banned_users = await ctx.guild.bans()
    member_name, member_discriminator = member.split('#')

    for ban_entry in banned_users:
        user = ban_entry.user
        if (user.name, user.discriminator) == (member_name, member_discriminator):
            await ctx.guild.unban(user)
            await ctx.send(f'Unbanned {user.mention}')
            return


## EVENTS
@bot.event
async def on_ready():
    print(f'{bot.user.name} Connected to Palac+ Discord')

@bot.event
async def on_member_join(member):
    welcome_message = f"""Hi {member.name}, welcome to Palac+ Discord server!
                     \nThis is a special discord channel where you can submit content requests to Palac+.
                     \nTo get started, submit a request by typing a command like this into the requests channel:
                     \n +request -movie <keyword1 keyword2 keyword3>  
                     \n +request -movie Napoleon Dynamite
                     \nFor additional help, type +help."""
    await member.create_dm()
    await member.dm_channel.send(welcome_message)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.semd('wut... try getting some +help')


@bot.event
async def on_error(event, *args, **kwargs):
    with open('err.log', 'a') as f:
        if event == 'on_message':
            f.write(f'Unhandled message: {args[0]}\n')
        else:
            print(event)


### ERRORS
@selfdestruct.error
async def selfdestruct_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Please specify an amount of messages to delete.')
    else:
        print(error)

@request.error
async def request_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Please specify the content type and title.\n EX: +request movie Napoleon Dynamite')
    else:
        print(error)

## OTHER





if __name__ == '__main__':
    bot.run(TOKEN)
