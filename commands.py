# This example requires the 'members' and 'message_content' privileged intents to function.

import os
import discord
from discord.ext import commands
import main
import re

description = '''Phoenix Rising family bot, Fawkes.'''

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='?', description=description, intents=intents)

@bot.event
async def on_command(ctx):
    await ctx.message.delete()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

@bot.command(name='isolm')
async def solInit(ctx):
    await main.sendInitMessage(ctx,'AETERNUM SOL','Sol')

@bot.command(name='iignism')
async def ignisInit(ctx):
    await main.sendInitMessage(ctx,'AETERNUM IGNIS','Ignis')

@bot.command(name='idustm')
async def dustInit(ctx):
    await main.sendInitMessage(ctx,'FROM THE DUST','Dust')

@bot.command(name='iashesm')
async def ashesInit(ctx):
    await main.sendInitMessage(ctx,'FROM THE ASHES','Ashes')

@bot.command(name='irebornm')
async def RebornInit(ctx):
    await main.sendInitMessage(ctx,'PHOENIX REBORN','Reborn')

@bot.command(name='irisenm')
async def RisenInit(ctx):
    await main.sendInitMessage(ctx,'PHOENIX RISEN','Risen')

@bot.command(name='iheliosm')
async def heliosInit(ctx):
    await main.sendInitMessage(ctx,'PHOENIX HELIOS','Helios')

@bot.command(name='inovam')
async def novaInit(ctx):
    await main.sendInitMessage(ctx,'PHOENIX NOVA','Nova')

@bot.command(name='ivulcanm')
async def vulcanInit(ctx):
    await main.sendInitMessage(ctx,'PHOENIX VULCAN','Vulcan')

@bot.command(name='inebulam')
async def nebulaInit(ctx):
    await main.sendInitMessage(ctx,'PHOENIX NEBULA','Nebula')

@bot.command(name='ititanm')
async def titanInit(ctx):
    await main.sendInitMessage(ctx,'PHOENIX TITAN','Titan')

@bot.command(name='ibootesm')
async def bootesInit(ctx):
    await main.sendInitMessage(ctx,'BOOTES VOID','Bootes')

@bot.command(name='iicem')
async def iceInit(ctx):
    await main.sendInitMessage(ctx,'PHOENIX ICE','Ice')

@bot.command(name='ifirem')
async def fireInit(ctx):
    await main.sendInitMessage(ctx,'PHOENIX FIRE','Fire')

@bot.command(name='idragonm')
async def dragonInit(ctx):
    await main.sendInitMessage(ctx,'PHOENIX DRAGON','Dragon')

@bot.command(name='iastram')
async def australasiaInit(ctx):
    await main.sendInitMessage(ctx,'PHOENIX AUSTRALASIA','Astra')

@bot.command(name='ikraken')
async def krakenInit(ctx):
    await main.sendInitMessage(ctx,'PHOENIX KRAKEN','Kraken')

@bot.command(name='firem')
async def firePlayers(ctx):
    await main.getPlayersResponse(ctx, main.rolesPerCrewAndColor['Fire'], "Phoenix Fire")

@bot.command(name='solm')
async def solPlayers(ctx):
    await main.getPlayersResponse(ctx, main.rolesPerCrewAndColor['Sol'], 'Aeternum Sol')

@bot.command(name='dustm')
async def dustPlayers(ctx):
    await main.getPlayersResponse(ctx, main.rolesPerCrewAndColor['Dust'], "From The Dust")

@bot.command(name='risenm')
async def risenPlayers(ctx):
    await main.getPlayersResponse(ctx, main.rolesPerCrewAndColor['Risen'], "Phoenix Risen")

@bot.command(name='dragonm')
async def dragonPlayers(ctx):
    await main.getPlayersResponse(ctx, main.rolesPerCrewAndColor['Dragon'], "Phoenix Dragon")

@bot.command(name='heliosm')
async def heliosPlayers(ctx):
    await main.getPlayersResponse(ctx, main.rolesPerCrewAndColor['Helios'], "Phoenix Helios")

@bot.command(name='vulcanm')
async def vulcanPlayers(ctx):
    await main.getPlayersResponse(ctx, main.rolesPerCrewAndColor['Vulcan'], "Phoenix Vulcan")

@bot.command(name='bootesm')
async def bootesPlayers(ctx):
    await main.getPlayersResponse(ctx, main.rolesPerCrewAndColor['Bootes'], "Bootes Void")

@bot.command(name='icem')
async def icePlayers(ctx):
    await main.getPlayersResponse(ctx, main.rolesPerCrewAndColor['Ice'], "Phoenix Ice")

@bot.command(name='ignism')
async def ignisPlayers(ctx):
    await main.getPlayersResponse(ctx, main.rolesPerCrewAndColor['Ignis'], "Aeternum Ignis")

@bot.command(name='ashesm')
async def ashesPlayers(ctx):
    await main.getPlayersResponse(ctx, main.rolesPerCrewAndColor['Ashes'], "From The Ashes")

@bot.command(name='nebulam')
async def nebulaPlayers(ctx):
    await main.getPlayersResponse(ctx, main.rolesPerCrewAndColor['Nebula'], "Phoenix Nebula")

@bot.command(name='novam')
async def novaPlayers(ctx):
    await main.getPlayersResponse(ctx, main.rolesPerCrewAndColor['Nova'], "Phoenix Nova")

@bot.command(name='rebornm')
async def rebornPlayers(ctx):
    await main.getPlayersResponse(ctx, main.rolesPerCrewAndColor['Reborn'], "Phoenix Reborn")

@bot.command(name='titanm')
async def titanPlayers(ctx):
    await main.getPlayersResponse(ctx, main.rolesPerCrewAndColor['Titan'], "Phoenix Titan")

@bot.command(name='krakenm')
async def krakenPlayers(ctx):
    await main.getPlayersResponse(ctx, main.rolesPerCrewAndColor['Kraken'], "Phoenix Kraken")

@bot.command(name='astram')
async def australasiaPlayers(ctx):
    await main.getPlayersResponse(ctx, main.rolesPerCrewAndColor['AustralAsia'], "Phoenix AustralAsia")

@bot.command(name='add')
async def add(ctx):
    for guild in bot.guilds:
        print(guild.id)

# @bot.command(name='kick')
# async def kick(ctx, user, *args):
#     reason = ' '.join(args)
#     await main.kickOrBanOrUnban(ctx, user, 'kick', bot, reason = reason)

# @bot.command(name='ban')
# async def ban(ctx, user, *args):
#     reason = ' '.join(args)
#     await main.kickOrBanOrUnban(ctx, user, 'ban', bot, reason=reason)

# @bot.command(name='unban')
# async def unban(ctx, user):
#     await main.kickOrBanOrUnban(ctx, user, 'unban', bot)

bot.run(os.environ.get("DISCORD_BOT_TOKEN"))