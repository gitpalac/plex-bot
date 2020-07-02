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

content_types = ['movie', 'tv-show']


## CHECKS
def check_request(ctx):
    return ctx.args[0] in content_types

## COMMANDS

@bot.command(name='request',
             description='Type this command to request content for Palac+',
             help='Plex requests',
             usage='<movie/tv-show> [title keywords]')
@commands.check(check_request)
async def request(ctx, content_type, *args):

    content_type = content_type.lower()
    payload = {'message_id' : ctx.message.id,
                'content_type' : content_type.strip('-'),
               'raw_content' : ctx.message.content,
               'keywords' : [k.lower() for k in args],
               'reaction_count' : len(ctx.message.reactions),
               'created_at' : ctx.message.created_at,
               'edited_at' : ctx.message.edited_at,
               'jump_url' : ctx.message.jump_url,
               'created_by' : ctx.message.author
               }
    await ctx.message.add_reaction('👍')
    response = f"""Request Accepted {ctx.author.display_name}.\n"""
    print(f'{ctx.author} added a request : {payload}')

    results = MediaClient(**payload)
    for movie in results.movies:
        if movie.image_url is not None:
            embed = discord.Embed(title=movie.title,
                                  description=movie.titleType,
                                  colour=discord.Colour.blue())
            embed.set_footer(text="React to this message to approve/deny submission")
            embed.set_image(url=movie.image_url)
            embed.set_thumbnail(url="https://ia.media-imdb.com/images/M/MV5BMTczNjM0NDY0Ml5BMl5BcG5nXkFtZTgwMTk1MzQ2OTE@._V1_.png")
            embed.set_author(name="Your submission",
                             icon_url="https://www.plex.tv/wp-content/uploads/2018/01/pmp-icon-1.png")
            embed.add_field(name="Year", value=movie.year, inline=True)
            embed.add_field(name="Length", value=f"{movie.runtime_hour}h {movie.runtime_min}min", inline=True)
            embed.add_field(name="Stars", value=', '.join(movie.actors[0:2]), inline=False)
            embedded_message = await ctx.send(response, embed=embed)
            await embedded_message.add_reaction('✅')
            await embedded_message.add_reaction('❌')
            break

    request_queue.append(payload)


@bot.command(name='hack',
             help='Do not try this.',
             usage='<member>')
@commands.has_permissions(kick_members=True)
async def hack(ctx, member : discord.Member):
    await member.create_dm()
    for _ in range(50):
        await member.dm_channel.send('LOL')


@bot.command(name='selfdestruct',
             help='Deletes messages',
             usage='<# of messages to delete>')
@commands.has_permissions(manage_messages=True)
async def selfdestruct(ctx, amount=1000):
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
        await ctx.semd('wut...')
        await ctx.send_help()


@bot.event
async def on_error(event, *args, **kwargs):
    with open('err.log', 'a') as f:
        f.write(f'Unhandled message: {args[0]}\n')

@bot.event
async def on_reaction_add(reaction, user):
    if not user.bot:
        if reaction.emoji == '❌':
            print(f'Message {reaction.message.id} removed from queue')
        elif reaction.emoji == '✅':
            print('YUP')
            bot.send(f'{user.name} Your movie selection was submitted')
            ##CHECKPOINT -- Submit to queue
            # -- confirm user reacting to submission is original submission author
            # -- and where the message ID matches the reacted message ID
        else:
            print('reaction ignored')


### ERRORS
@selfdestruct.error
async def selfdestruct_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Please specify an amount of messages to delete.')
    else:
        await ctx.send_help()
        print(error)

@request.error
async def request_error(ctx, error):
    await ctx.message.clear_reaction('👍')
    await ctx.message.add_reaction('👎')
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Please specify the content type and title.\n EX: +request movie Napoleon Dynamite')
    else:
        await ctx.send_help()
        print(error)

@hack.error
async def hack_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        response = f'Access Denied'
        await ctx.send(response, tts=True)
        await ctx.message.add_reaction('🤡')
    else:
        print(error)
        ctx.send_help()

## OTHER



if __name__ == '__main__':
    bot.run(TOKEN)
