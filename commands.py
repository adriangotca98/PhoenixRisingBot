import discord
from discord.ext import commands
import main

description = '''Phoenix Rising family bot, Fawkes.'''

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = discord.Bot(description=description, intents=intents)

@bot.event
async def on_ready():
    await main.init(bot)
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

@bot.event
async def on_application_command_error(ctx, error):
    if isinstance(error, commands.MissingRole) or isinstance(error, commands.MissingPermissions):
        await ctx.send_response("<@"+str(ctx.author.id)+">, you're not authorized to use this command! Only leadership can use this. Thank you :) ", ephemeral=True)
        return
    await ctx.send_response(f"An unexpected error has occured. <@308561593858392065>, please have a look in the code. Command run: {ctx.command.name}")
    raise error

@bot.slash_command(name="members", description="Used to get members of a certain crew")
@commands.has_role("Phoenix Family Leadership")
@discord.option(
    "crew_name",
    description='Crew for which you want to create/update list of members',
    required=True,
    choices=['alpha','dust','ashes','fire','ice','dragon','risen','vulcan','helios','bootes','reborn','nebula','titan','kraken','ignis','nova','astra']
)
async def getMembers(ctx: discord.ApplicationContext, crew_name: str):
    await main.getPlayersResponse(ctx, crew_name)
    await ctx.send_response("OK, all good!", ephemeral=True)

@bot.slash_command(name='score', description='Set score for the crew in the CREW TABLES section and reorder the channels by score.')
@commands.has_role("Phoenix Family Leadership")
@discord.option(
    "crew_name",
    description='Crew for which you want to update score',
    required=True,
    choices=['alpha','dust','ashes','fire','ice','dragon','risen','vulcan','helios','bootes','reborn','nebula','titan','kraken','ignis','nova','astra']
)
@discord.option(
    "score",
    type=int,
    required=True
)
async def setScoreForCrew(ctx: discord.ApplicationContext, crew_name: str, score: int):
    scoreStr = str(score)
    await main.setScore(ctx, crew_name, scoreStr)
    await ctx.send_response("Score updated :)",ephemeral=True)

@bot.slash_command(name='kick', description='Kick a member from all servers (Rising, Knowing, Racing, Servering).')
@commands.has_permissions(kick_members=True)
@discord.option(
    "user",
    description='user to kick',
    required=True,
    input_type=discord.Member
)
async def kick(ctx: discord.ApplicationContext, user: discord.Member, reason: str):
    await main.kickOrBanOrUnban(user, 'kick', bot, reason = reason)
    await ctx.send_response("User kicked :)",ephemeral=True)

@bot.slash_command(name='ban',description='Ban a member from all servers (Rising, Knowing, Racing, Servering).')
@commands.has_permissions(ban_members=True)
@discord.option(
    "user",
    description='user to ban',
    required=True,
    input_type=discord.Member
)
async def ban(ctx: discord.ApplicationContext, user: discord.Member, reason: str):
    await main.kickOrBanOrUnban(user, 'ban', bot, reason=reason)
    await ctx.send_response("User banned :)", ephemeral=True)

@bot.slash_command(name='unban', description='Unban a former member from all servers.')
@commands.has_permissions(ban_members=True)
@discord.option(
    "user",
    description='user to unban',
    required=True,
    input_type=discord.Member
)
async def unban(ctx: discord.ApplicationContext, user: discord.Member):
    await main.kickOrBanOrUnban(user, 'unban', bot)
    await ctx.send_response("User unbanned :)", ephemeral=True)

bot.run(main.discord_bot_token)