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

@bot.command(name='firem')
@commands.has_role("Phoenix Family Leadership")
async def firePlayers(ctx):
    await main.getPlayersResponse(ctx, 'Fire')

@bot.command(name='solm')
@commands.has_role("Phoenix Family Leadership")
async def solPlayers(ctx):
    await main.getPlayersResponse(ctx, 'Sol')

@bot.command(name='dustm')
@commands.has_role("Phoenix Family Leadership")
async def dustPlayers(ctx):
    await main.getPlayersResponse(ctx, 'Dust')

@bot.command(name='risenm')
@commands.has_role("Phoenix Family Leadership")
async def risenPlayers(ctx):
    await main.getPlayersResponse(ctx, 'Risen')

@bot.command(name='dragonm')
@commands.has_role("Phoenix Family Leadership")
async def dragonPlayers(ctx):
    await main.getPlayersResponse(ctx, 'Dragon')

@bot.command(name='heliosm')
@commands.has_role("Phoenix Family Leadership")
async def heliosPlayers(ctx):
    await main.getPlayersResponse(ctx, 'Helios')

@bot.command(name='vulcanm')
@commands.has_role("Phoenix Family Leadership")
async def vulcanPlayers(ctx):
    await main.getPlayersResponse(ctx, 'Vulcan')

@bot.command(name='bootesm')
@commands.has_role("Phoenix Family Leadership")
async def bootesPlayers(ctx):
    await main.getPlayersResponse(ctx, 'Bootes')

@bot.command(name='icem')
@commands.has_role("Phoenix Family Leadership")
async def icePlayers(ctx):
    await main.getPlayersResponse(ctx, 'Ice')

@bot.command(name='ignism')
@commands.has_role("Phoenix Family Leadership")
async def ignisPlayers(ctx):
    await main.getPlayersResponse(ctx, 'Ignis')

@bot.command(name='ashesm')
@commands.has_role("Phoenix Family Leadership")
async def ashesPlayers(ctx):
    await main.getPlayersResponse(ctx, 'Ashes')

@bot.command(name='nebulam')
@commands.has_role("Phoenix Family Leadership")
async def nebulaPlayers(ctx):
    await main.getPlayersResponse(ctx, 'Nebula')

@bot.command(name='novam')
@commands.has_role("Phoenix Family Leadership")
async def novaPlayers(ctx):
    await main.getPlayersResponse(ctx, 'Nova')

@bot.command(name='rebornm')
@commands.has_role("Phoenix Family Leadership")
async def rebornPlayers(ctx):
    await main.getPlayersResponse(ctx, 'Reborn')

@bot.command(name='titanm')
@commands.has_role("Phoenix Family Leadership")
async def titanPlayers(ctx):
    await main.getPlayersResponse(ctx, 'Titan')

@bot.command(name='krakenm')
@commands.has_role("Phoenix Family Leadership")
async def krakenPlayers(ctx):
    await main.getPlayersResponse(ctx, 'Kraken')

@bot.command(name='astram')
@commands.has_role("Phoenix Family Leadership")
async def australasiaPlayers(ctx):
    await main.getPlayersResponse(ctx, 'Astra')

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