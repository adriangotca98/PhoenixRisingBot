# This example requires the 'members' and 'message_content' privileged intents to function.

import os
import discord
from discord.ext import commands
import main

description = '''Phoenix Rising family bot, Fawkes.'''

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='?', description=description, intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

@bot.command(name='i_sol')
async def solInit(ctx):
    await main.sendInitMessage(ctx,'AETERNUM SOL','Sol')

@bot.command(name='i_ignis')
async def ignisInit(ctx):
    await main.sendInitMessage(ctx,'AETERNUM IGNIS','Ignis')

@bot.command(name='i_dust')
async def dustInit(ctx):
    await main.sendInitMessage(ctx,'FROM THE DUST','Dust')

@bot.command(name='i_ashes')
async def ashesInit(ctx):
    await main.sendInitMessage(ctx,'FROM THE ASHES','Ashes')

@bot.command(name='i_reborn')
async def RebornInit(ctx):
    await main.sendInitMessage(ctx,'PHOENIX REBORN','Reborn')

@bot.command(name='i_risen')
async def RisenInit(ctx):
    await main.sendInitMessage(ctx,'PHOENIX RISEN','Risen')

@bot.command(name='i_helios')
async def heliosInit(ctx):
    await main.sendInitMessage(ctx,'PHOENIX HELIOS','Helios')

@bot.command(name='i_nova')
async def novaInit(ctx):
    await main.sendInitMessage(ctx,'PHOENIX NOVA','Nova')

@bot.command(name='i_vulcan')
async def vulcanInit(ctx):
    await main.sendInitMessage(ctx,'PHOENIX VULCAN','Vulcan')

@bot.command(name='i_nebula')
async def nebulaInit(ctx):
    await main.sendInitMessage(ctx,'PHOENIX NEBULA','Nebula')

@bot.command(name='i_titan')
async def titanInit(ctx):
    await main.sendInitMessage(ctx,'PHOENIX TITAN','Titan')

@bot.command(name='i_bootes')
async def bootesInit(ctx):
    await main.sendInitMessage(ctx,'BOOTES VOID','Bootes')

@bot.command(name='i_ice')
async def iceInit(ctx):
    await main.sendInitMessage(ctx,'PHOENIX ICE','Ice')

@bot.command(name='i_fire')
async def fireInit(ctx):
    await main.sendInitMessage(ctx,'PHOENIX FIRE','Fire')

@bot.command(name='i_dragon')
async def dragonInit(ctx):
    await main.sendInitMessage(ctx,'PHOENIX DRAGON','Dragon')

@bot.command(name='i_astra')
async def australasiaInit(ctx):
    await main.sendInitMessage(ctx,'PHOENIX AUSTRALASIA','Astra')

@bot.command(name='i_kraken')
async def krakenInit(ctx):
    await main.sendInitMessage(ctx,'PHOENIX KRAKEN','Kraken')

@bot.command(name='m_fire')
async def firePlayers(ctx):
    await main.getPlayersResponse(ctx, main.rolesPerCrewAndColor['Fire'], "Phoenix Fire")

@bot.command(name='m_sol')
async def solPlayers(ctx):
    await main.getPlayersResponse(ctx, main.rolesPerCrewAndColor['Sol'], 'Aeternum Sol')

@bot.command(name='m_dust')
async def dustPlayers(ctx):
    await main.getPlayersResponse(ctx, main.rolesPerCrewAndColor['Dust'], "From The Dust")

@bot.command(name='m_risen')
async def risenPlayers(ctx):
    await main.getPlayersResponse(ctx, main.rolesPerCrewAndColor['Risen'], "Phoenix Risen")

@bot.command(name='m_dragon')
async def dragonPlayers(ctx):
    await main.getPlayersResponse(ctx, main.rolesPerCrewAndColor['Dragon'], "Phoenix Dragon")

@bot.command(name='m_helios')
async def heliosPlayers(ctx):
    await main.getPlayersResponse(ctx, main.rolesPerCrewAndColor['Helios'], "Phoenix Helios")

@bot.command(name='m_vulcan')
async def vulcanPlayers(ctx):
    await main.getPlayersResponse(ctx, main.rolesPerCrewAndColor['Vulcan'], "Phoenix Vulcan")

@bot.command(name='m_bootes')
async def bootesPlayers(ctx):
    await main.getPlayersResponse(ctx, main.rolesPerCrewAndColor['Bootes'], "Bootes Void")

@bot.command(name='m_ice')
async def icePlayers(ctx):
    await main.getPlayersResponse(ctx, main.rolesPerCrewAndColor['Ice'], "Phoenix Ice")

@bot.command(name='m_ignis')
async def ignisPlayers(ctx):
    await main.getPlayersResponse(ctx, main.rolesPerCrewAndColor['Ignis'], "Aeternum Ignis")

@bot.command(name='m_ashes')
async def ashesPlayers(ctx):
    await main.getPlayersResponse(ctx, main.rolesPerCrewAndColor['Ashes'], "From The Ashes")

@bot.command(name='m_nebula')
async def nebulaPlayers(ctx):
    await main.getPlayersResponse(ctx, main.rolesPerCrewAndColor['Nebula'], "Phoenix Nebula")

@bot.command(name='m_nova')
async def novaPlayers(ctx):
    await main.getPlayersResponse(ctx, main.rolesPerCrewAndColor['Nova'], "Phoenix Nova")

@bot.command(name='m_reborn')
async def rebornPlayers(ctx):
    await main.getPlayersResponse(ctx, main.rolesPerCrewAndColor['Reborn'], "Phoenix Reborn")

@bot.command(name='m_titan')
async def titanPlayers(ctx):
    await main.getPlayersResponse(ctx, main.rolesPerCrewAndColor['Titan'], "Phoenix Titan")

@bot.command(name='m_kraken')
async def krakenPlayers(ctx):
    await main.getPlayersResponse(ctx, main.rolesPerCrewAndColor['Kraken'], "Phoenix Kraken")

@bot.command(name='m_astra')
async def australasiaPlayers(ctx):
    await main.getPlayersResponse(ctx, main.rolesPerCrewAndColor['AustralAsia'], "Phoenix AustralAsia")

bot.run(os.environ.get("DISCORD_BOT_TOKEN"))