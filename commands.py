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
    bot.commands[0].checks[0]

async def getOptionStr(ctx: discord.ApplicationContext, option):
    try:
        value=option['value']
        id=int(value)
        member=await ctx.guild.fetch_member(id)
        return f'{member.name}#{member.discriminator}'
    except:
        return str(option['value'])

@bot.event
async def on_application_command_completion(ctx: discord.ApplicationContext):
    args = ''
    if ctx.selected_options is not None:
        for option in ctx.selected_options:
            optionStr = await getOptionStr(ctx, option)+" "
            args+=optionStr
    message = f"**{ctx.author.name}#{ctx.author.discriminator}** has sent the following command: **/{ctx.command.name} {args}**"
    await (await bot.fetch_channel(main.loggingChannelId)).send(message)

@bot.event
async def on_application_command_error(ctx: discord.ApplicationContext, error):
    if isinstance(error, commands.MissingRole) or isinstance(error, commands.MissingPermissions):
        await ctx.send_followup("<@"+str(ctx.author.id)+">, you're not authorized to use this command! Only leadership can use this. Thank you :) ", ephemeral=True)
        return
    await ctx.send_followup(f"Failed unexpectedly")
    await ctx.send(f"An unexpected error has occured. <@308561593858392065>, please have a look in the code. Command run: {ctx.command.name}")
    args = " ".join([(await getOptionStr(ctx, option)) for option in ctx.selected_options])
    message = f"**{ctx.author.name}#{ctx.author.discriminator}** tried to send the following command: **/{ctx.command.name} {args}**, but it errored out."
    await (await bot.fetch_channel(main.loggingChannelId)).send(message)
    raise error

@bot.slash_command(name="members", description="Used to get members of a certain crew", guild_ids=[main.risingServerId])
@commands.has_role("Phoenix Family Leadership")
@discord.option(
    "crew_name",
    description='Crew for which you want to create/update list of members',
    required=True,
    choices=main.getCrewNames()
)
async def getMembers(ctx: discord.ApplicationContext, crew_name: str):
    await ctx.defer(ephemeral=True)
    message = await main.getPlayersResponse(ctx, crew_name)
    await ctx.send_followup(message, ephemeral=True)

@bot.slash_command(name='score', description='Set score for the crew in the CREW TABLES section and reorder the channels by score.', guild_ids=[main.risingServerId])
@commands.has_role("Phoenix Family Leadership")
@discord.option(
    "crew_name",
    description='Crew for which you want to update score',
    required=True,
    choices=main.getCrewNames()
)
@discord.option(
    "score",
    type=int,
    required=True
)
async def setScoreForCrew(ctx: discord.ApplicationContext, crew_name: str, score: int):
    await ctx.defer(ephemeral=True)
    scoreStr = str(score)
    await main.setScore(ctx, crew_name, scoreStr)
    await ctx.send_followup("Score updated :)",ephemeral=True)

@bot.slash_command(name='kick', description='Kick a member from all servers (Rising, Knowing, Racing, Servering).', guild_ids=[main.risingServerId, main.racingServerId, main.knowingServerId, main.serveringServerId])
@commands.has_permissions(kick_members=True)
@discord.option(
    "user",
    description='user to kick',
    required=True,
    input_type=discord.Member
)
async def kick(ctx: discord.ApplicationContext, user: discord.Member, reason: str):
    await ctx.defer(ephemeral=True)
    await main.kickOrBanOrUnban(user, 'kick', bot, reason = reason)
    await ctx.send_followup("User kicked :)",ephemeral=True)

@bot.slash_command(name='ban',description='Ban a member from all servers (Rising, Knowing, Racing, Servering).', guild_ids=[main.risingServerId, main.racingServerId, main.knowingServerId, main.serveringServerId])
@commands.has_permissions(ban_members=True)
@discord.option(
    "user",
    description='user to ban',
    required=True,
    input_type=discord.Member
)
async def ban(ctx: discord.ApplicationContext, user: discord.Member, reason: str):
    await ctx.defer(ephemeral=True)
    await main.kickOrBanOrUnban(user, 'ban', bot, reason=reason)
    await ctx.send_followup("User banned :)", ephemeral=True)

@bot.slash_command(name='unban', description='Unban a former member from all servers.', guild_ids=[main.risingServerId, main.racingServerId, main.knowingServerId, main.serveringServerId])
@commands.has_permissions(ban_members=True)
@discord.option(
    "user",
    description='user to unban',
    required=True,
    input_type=discord.Member
)
async def unban(ctx: discord.ApplicationContext, user: discord.Member):
    await ctx.defer(ephemeral=True)
    await main.kickOrBanOrUnban(user, 'unban', bot)
    await ctx.send_followup("User unbanned :)", ephemeral=True)

@bot.slash_command(name="multiple", description="Keep track of multiple accounts of the same person (same discord profile) within the same crew", guild_ids=[main.risingServerId])
@commands.has_role("Phoenix Family Leadership")
@discord.option(
    "user",
    description='user that has multiple accounts in the crew (not multiple accounts in the family!)',
    required=True,
    input_type=discord.Member
)
@discord.option(
    "crew_name",
    description='Crew where the player has multiple accounts',
    required=True,
    choices=main.getCrewNames()
)
@discord.option(
    "number_of_accounts",
    description='Number of accounts that the player has in that crew.',
    required=True,
    input_type=int
)
async def multiple(ctx: discord.ApplicationContext, user: discord.Member, crew_name: str, number_of_accounts: int):
    await ctx.defer(ephemeral=True)
    message = main.processMultiple(user, crew_name, number_of_accounts)
    await ctx.send_followup(message, ephemeral = True)

@bot.slash_command(name="transfer", description="Register a transfer for next season.", guild_ids=[main.risingServerId])
@commands.has_role("Phoenix Family Leadership")
@discord.option(
    "player",
    description="Tag the player that is moving",
    required=True,
    input_type=discord.Member
)
@discord.option(
    "crew_from",
    description="Crew which the player is leaving from",
    required=True,
    choices=['New to family'] + main.getCrewNames()
)
@discord.option(
    "crew_to",
    description="Crew where the player is going to",
    required=True,
    choices=['Out of family'] + main.getCrewNames()
)
@discord.option(
    "season",
    description="Season when the player will join the destination crew. Run /season for getting current season.",
    required=True,
    input_type=int
)
@discord.option(
    "number_of_accounts",
    description="Number of accounts the player is moving in this transfer.",
    required=False,
    input_type = int
)
async def transfer(ctx: discord.ApplicationContext, player: discord.Member, crew_from: str, crew_to: str, season: int, number_of_accounts: int):
    await ctx.defer(ephemeral=True)
    message = await main.processTransfer(ctx, player, crew_from, crew_to, number_of_accounts, season)
    await ctx.send_followup(message, ephemeral = True)

@bot.slash_command(name='current_season', description="Gets the current season we're in", guild_ids=[main.risingServerId])
@commands.has_role('Phoenix Rising')
async def current_season(ctx: discord.ApplicationContext):
    await ctx.send_response(str(main.getCurrentSeason()), ephemeral=True)

@bot.slash_command(name="cancel_transfer", description="unregisters a transfer in case of change of plans",guild_ids=[main.risingServerId])
@commands.has_role("Phoenix Family Leadership")
@discord.option(
    "player",
    description="Player for which you want to unregister the transfer",
    required=True,
    input_type=discord.Member
)
@discord.option(
    "crew_from",
    description="Crew which the player is planned to leave. Required if the player is involved in multiple transfers.",
    required=False,
    choices=['New to family'] + main.getCrewNames()
)
@discord.option(
    "crew_to",
    description="Crew which the player is planned to join. Required if the player is involved in multiple transfers.",
    required=False,
    choices=['Out of family'] + main.getCrewNames()
)
async def cancel_transfer(ctx: discord.ApplicationContext, player: discord.Member, crew_from=None, crew_to=None):
    await ctx.defer(ephemeral=True)
    message = await main.unregisterTransfer(ctx, player, crew_from, crew_to)
    await ctx.send_followup(message, ephemeral = True)

bot.run(main.discord_bot_token)