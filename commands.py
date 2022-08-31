# This example requires the 'members' and 'message_content' privileged intents to function.

import os
import discord
from discord.ext import commands
import main

description = '''Phoenix Rising family bot, Fawkes.'''

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', description=description, intents=intents)

@bot.event
async def on_command(ctx):
    await ctx.message.delete()

@bot.event
async def on_ready():
    await main.init(bot)
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

@bot.event
async def on_command_error(ctx: commands.Context, error):
    if isinstance(error, commands.errors.MissingRole) or isinstance(error, commands.errors.MissingPermissions):
        await ctx.send("<@"+str(ctx.author.id)+">, you're not authorized to use this command! Only leadership can use this. Thank you :) ")
        return
    if isinstance(error, commands.CommandNotFound):
        return
    await ctx.send(f"An unexpected error has occured. <@308561593858392065>, please have a look in the code. Command run: {ctx.command.name}")
    raise error

@bot.command(name='solmm')
@commands.has_role("Phoenix Family Leadership")
async def solInit(ctx):
    await main.sendInitMessage(ctx,'AETERNUM SOL','Sol')

@bot.command(name='ignismm')
@commands.has_role("Phoenix Family Leadership")
async def ignisInit(ctx):
    await main.sendInitMessage(ctx,'AETERNUM IGNIS','Ignis')

@bot.command(name='dustmm')
@commands.has_role("Phoenix Family Leadership")
async def dustInit(ctx):
    await main.sendInitMessage(ctx,'FROM THE DUST','Dust')

@bot.command(name='ashesmm')
@commands.has_role("Phoenix Family Leadership")
async def ashesInit(ctx):
    await main.sendInitMessage(ctx,'FROM THE ASHES','Ashes')

@bot.command(name='rebornmm')
@commands.has_role("Phoenix Family Leadership")
async def RebornInit(ctx):
    await main.sendInitMessage(ctx,'PHOENIX REBORN','Reborn')

@bot.command(name='risenmm')
@commands.has_role("Phoenix Family Leadership")
async def RisenInit(ctx):
    await main.sendInitMessage(ctx,'PHOENIX RISEN','Risen')

@bot.command(name='heliosmm')
@commands.has_role("Phoenix Family Leadership")
async def heliosInit(ctx):
    await main.sendInitMessage(ctx,'PHOENIX HELIOS','Helios')

@bot.command(name='novamm')
@commands.has_role("Phoenix Family Leadership")
async def novaInit(ctx):
    await main.sendInitMessage(ctx,'PHOENIX NOVA','Nova')

@bot.command(name='vulcanmm')
@commands.has_role("Phoenix Family Leadership")
async def vulcanInit(ctx):
    await main.sendInitMessage(ctx,'PHOENIX VULCAN','Vulcan')

@bot.command(name='nebulamm')
@commands.has_role("Phoenix Family Leadership")
async def nebulaInit(ctx):
    await main.sendInitMessage(ctx,'PHOENIX NEBULA','Nebula')

@bot.command(name='titanmm')
@commands.has_role("Phoenix Family Leadership")
async def titanInit(ctx):
    await main.sendInitMessage(ctx,'PHOENIX TITAN','Titan')

@bot.command(name='bootesmm')
@commands.has_role("Phoenix Family Leadership")
async def bootesInit(ctx):
    await main.sendInitMessage(ctx,'BOOTES VOID','Bootes')

@bot.command(name='icemm')
@commands.has_role("Phoenix Family Leadership")
async def iceInit(ctx):
    await main.sendInitMessage(ctx,'PHOENIX ICE','Ice')

@bot.command(name='firemm')
@commands.has_role("Phoenix Family Leadership")
async def fireInit(ctx):
    await main.sendInitMessage(ctx,'PHOENIX FIRE','Fire')

@bot.command(name='dragonmm')
@commands.has_role("Phoenix Family Leadership")
async def dragonInit(ctx):
    await main.sendInitMessage(ctx,'PHOENIX DRAGON','Dragon')

@bot.command(name='astramm')
@commands.has_role("Phoenix Family Leadership")
async def australasiaInit(ctx):
    await main.sendInitMessage(ctx,'PHOENIX AUSTRALASIA','Astra')

@bot.command(name='krakenmm')
@commands.has_role("Phoenix Family Leadership")
async def krakenInit(ctx):
    await main.sendInitMessage(ctx,'PHOENIX KRAKEN','Kraken')

@bot.command(name='firem')
@commands.has_role("Phoenix Family Leadership")
async def firePlayers(ctx):
    await main.getPlayersResponse(ctx, main.crewData['Fire'], "Phoenix Fire")

@bot.command(name='solm')
@commands.has_role("Phoenix Family Leadership")
async def solPlayers(ctx):
    await main.getPlayersResponse(ctx, main.crewData['Sol'], 'Aeternum Sol')

@bot.command(name='dustm')
@commands.has_role("Phoenix Family Leadership")
async def dustPlayers(ctx):
    await main.getPlayersResponse(ctx, main.crewData['Dust'], "From The Dust")

@bot.command(name='risenm')
@commands.has_role("Phoenix Family Leadership")
async def risenPlayers(ctx):
    await main.getPlayersResponse(ctx, main.crewData['Risen'], "Phoenix Risen")

@bot.command(name='dragonm')
@commands.has_role("Phoenix Family Leadership")
async def dragonPlayers(ctx):
    await main.getPlayersResponse(ctx, main.crewData['Dragon'], "Phoenix Dragon")

@bot.command(name='heliosm')
@commands.has_role("Phoenix Family Leadership")
async def heliosPlayers(ctx):
    await main.getPlayersResponse(ctx, main.crewData['Helios'], "Phoenix Helios")

@bot.command(name='vulcanm')
@commands.has_role("Phoenix Family Leadership")
async def vulcanPlayers(ctx):
    await main.getPlayersResponse(ctx, main.crewData['Vulcan'], "Phoenix Vulcan")

@bot.command(name='bootesm')
@commands.has_role("Phoenix Family Leadership")
async def bootesPlayers(ctx):
    await main.getPlayersResponse(ctx, main.crewData['Bootes'], "Bootes Void")

@bot.command(name='icem')
@commands.has_role("Phoenix Family Leadership")
async def icePlayers(ctx):
    await main.getPlayersResponse(ctx, main.crewData['Ice'], "Phoenix Ice")

@bot.command(name='ignism')
@commands.has_role("Phoenix Family Leadership")
async def ignisPlayers(ctx):
    await main.getPlayersResponse(ctx, main.crewData['Ignis'], "Aeternum Ignis")

@bot.command(name='ashesm')
@commands.has_role("Phoenix Family Leadership")
async def ashesPlayers(ctx):
    await main.getPlayersResponse(ctx, main.crewData['Ashes'], "From The Ashes")

@bot.command(name='nebulam')
@commands.has_role("Phoenix Family Leadership")
async def nebulaPlayers(ctx):
    await main.getPlayersResponse(ctx, main.crewData['Nebula'], "Phoenix Nebula")

@bot.command(name='novam')
@commands.has_role("Phoenix Family Leadership")
async def novaPlayers(ctx):
    await main.getPlayersResponse(ctx, main.crewData['Nova'], "Phoenix Nova")

@bot.command(name='rebornm')
@commands.has_role("Phoenix Family Leadership")
async def rebornPlayers(ctx):
    await main.getPlayersResponse(ctx, main.crewData['Reborn'], "Phoenix Reborn")

@bot.command(name='titanm')
@commands.has_role("Phoenix Family Leadership")
async def titanPlayers(ctx):
    await main.getPlayersResponse(ctx, main.crewData['Titan'], "Phoenix Titan")

@bot.command(name='krakenm')
@commands.has_role("Phoenix Family Leadership")
async def krakenPlayers(ctx):
    await main.getPlayersResponse(ctx, main.crewData['Kraken'], "Phoenix Kraken")

@bot.command(name='astram')
@commands.has_role("Phoenix Family Leadership")
async def australasiaPlayers(ctx):
    await main.getPlayersResponse(ctx, main.crewData['Astra'], "Phoenix AustralAsia")

@bot.command(name='score')
#@commands.has_role("Phoenix Family Leadership")
async def setScoreForCrew(ctx: commands.Context, crewName: str, score: str):
    print(crewName, score)
    await main.setScore(ctx, crewName, score)

@bot.command(name='add')
@commands.has_role("Phoenix Family Leadership")
async def add(ctx: commands.Context):
    print(ctx.channel.category)
    print(ctx.permissions.kick_members)
    print(ctx.permissions.ban_members)

@bot.command(name='kick')
@commands.has_permissions(kick_members=True)
async def kick(ctx, user, *args):
    reason = ' '.join(args)
    await main.kickOrBanOrUnban(user, 'kick', bot, reason = reason)

@bot.command(name='ban')
@commands.has_permissions(ban_members=True)
async def ban(ctx, user, *args):
    reason = ' '.join(args)
    await main.kickOrBanOrUnban(user, 'ban', bot, reason=reason)

@bot.command(name='unban')
@commands.has_permissions(ban_members=True)
async def unban(ctx, user):
    await main.kickOrBanOrUnban(user, 'unban', bot)

bot.run(os.environ.get("DISCORD_BOT_TOKEN"))