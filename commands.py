import discord
from discord.ext import commands
import main
import views

description = '''Phoenix Rising family bot, Fawkes.'''

intents = discord.Intents.default()

bot = discord.Bot(description=description, intents=intents)


@bot.event
async def on_ready():
    await main.init(bot)
    print(f'Logged in as {bot.user} (ID: {bot.user.id if bot.user is not None else 0})')
    print('------')


async def getOptionStr(ctx: discord.ApplicationContext, option):
    try:
        value = option['value']
        member_id = int(value)
        member = await ctx.bot.fetch_user(member_id)
        if member.discriminator != 0:
            return f'{member.name}#{member.discriminator}'
        return f'{member.name}'
    except discord.Forbidden or discord.HTTPException:
        return str(option['value'])
    except ValueError:
        return str(option['value'])


@bot.event
async def on_application_command_completion(ctx: discord.ApplicationContext):
    args = ''
    if ctx.selected_options is not None:
        for option in ctx.selected_options:
            option_str = await getOptionStr(ctx, option) + " "
            args += option_str
    if ctx.author is not None:
        discriminator = f"#{ctx.author.discriminator}" if ctx.author.discriminator != "0" else ""
        message = (f"**{ctx.author.name}{discriminator}** has sent the following command:"
                   f"**/{ctx.command.name} {args}**")
        channel = await bot.fetch_channel(main.loggingChannelId)
        if isinstance(channel, discord.TextChannel):
            await channel.send(message)


@bot.event
async def on_application_command_error(ctx: discord.ApplicationContext, error):
    if isinstance(error, commands.MissingRole) or isinstance(error, commands.MissingPermissions):
        if ctx.author is not None:
            await ctx.send_response("<@" + str(
                ctx.author.id) + ">, you're not authorized to use this command! Only leadership can use this. Thank "
                                 "you :) ",
                                    ephemeral=True)
        return
    await ctx.send(
        f"An unexpected error has occurred. <@308561593858392065>, please have a look in the code. "
        f"Command run: {ctx.command.name}")
    args = None
    if ctx.selected_options is not None:
        args = " ".join([(await getOptionStr(ctx, option)) for option in ctx.selected_options])
    if ctx.author is not None:
        discriminator = f"#{ctx.author.discriminator}" if ctx.author.discriminator != "0" else ""
        message = (f"**{ctx.author.name}{discriminator}** tried to send the following command: "
                   f"**/{ctx.command.name} {args}**, but it error out.")
        channel = await bot.fetch_channel(main.loggingChannelId)
        if isinstance(channel, discord.TextChannel):
            await channel.send(message)
    try:
        await ctx.send_followup(f"Failed unexpectedly", ephemeral=True)
    except RuntimeError:
        await ctx.send("Failed unexpectedly")
    raise error


@bot.slash_command(name="new_members", description="Refresh the members list for a given crew",
                   guild_ids=[main.risingServerId])
@commands.has_any_role("Phoenix Family Leadership", "Fawkes Access")
async def new_members(ctx: discord.ApplicationContext):
    await ctx.send_response(" ", view=views.MembersCrewsView(ctx), ephemeral=True, delete_after=600)


@bot.slash_command(name="new_multiple", description="Register a player with multiple accounts in a single crew",
                   guild_ids=[main.risingServerId])
@commands.has_any_role("Phoenix Family Leadership", "Fawkes Access")
async def new_multiple(ctx: discord.ApplicationContext):
    await ctx.send_response(" ", view=views.MultipleView(ctx), ephemeral=True, delete_after=600)


@bot.slash_command(name="new_score", description="Sets a score for the crew given", guild_ids=[main.risingServerId])
@commands.has_any_role("Phoenix Family Leadership", "Fawkes Access")
async def new_score(ctx: discord.ApplicationContext):
    await ctx.send_response(" ", view=views.ScoreView(ctx), ephemeral=True, delete_after=600)


@bot.slash_command(name="new_ban", description="Bans a user")
@commands.has_permissions(ban_members=True)
async def new_ban(ctx: discord.ApplicationContext):
    await ctx.send_response(" ", view=views.KickBanUnbanView(ctx, bot, "ban"), ephemeral=True, delete_after=600)


@bot.slash_command(name="new_unban", description="Unbans a user")
@commands.has_permissions(ban_members=True)
async def new_unban(ctx: discord.ApplicationContext):
    await ctx.send_response(" ", view=views.KickBanUnbanView(ctx, bot, "unban"), ephemeral=True, delete_after=600)


@bot.slash_command(name="new_kick", description="Kicks a user")
@commands.has_permissions(kick_members=True)
async def new_kick(ctx: discord.ApplicationContext):
    await ctx.send_response(" ", view=views.KickBanUnbanView(ctx, bot, "kick"), ephemeral=True, delete_after=600)


@bot.slash_command(name="new_transfer", description="Used to register a transfer")
@commands.has_any_role("Phoenix Family Leadership", "Fawkes Access")
async def new_transfer(ctx: discord.ApplicationContext):
    await ctx.send_response(" ", view=views.TransferView(ctx), ephemeral=True, delete_after=600)


@bot.slash_command(name="new_cancel_transfer", description='Used to cancel a transfer')
@commands.has_any_role("Phoenix Family Leadership", "Fawkes Access")
async def new_cancel_transfer(ctx: discord.ApplicationContext):
    await ctx.send_response(" ", view=views.CancelTransferView(ctx), ephemeral=True, delete_after=600)


@bot.slash_command(name="make_transfers",
                   description="Used to process all transfers from last season or a given season.",
                   guild_ids=[main.risingServerId])
@commands.has_any_role("Phoenix Family Leadership", "Fawkes Access")
async def makeTransfers(ctx: discord.ApplicationContext):
    await ctx.defer(ephemeral=True)
    message = await main.makeTransfers(ctx)
    await ctx.send_followup(message, ephemeral=True, delete_after=60)


@bot.slash_command(name="members", description="Used to get members of a certain crew", guild_ids=[main.risingServerId])
@commands.has_any_role("Phoenix Family Leadership", "Fawkes Access")
@discord.option(
    "crew_name",
    description='Crew for which you want to create/update list of members',
    required=True,
    choices=main.getCrewNames()
)
async def getMembers(ctx: discord.ApplicationContext, crew_name: str):
    await ctx.defer(ephemeral=True)
    message = await main.getPlayersResponse(ctx, crew_name)
    await ctx.send_followup(message, ephemeral=True, delete_after=60)


@bot.slash_command(name='score',
                   description='Set score for the crew in the CREW TABLES section and reorder the channels by score.',
                   guild_ids=[main.risingServerId])
@commands.has_any_role("Phoenix Family Leadership", "Fawkes Access")
@discord.option(
    "crew_name",
    description='Crew for which you want to update score',
    required=True,
    choices=main.getCrewNames()
)
@discord.option(
    "score",
    input_type=int,
    required=True
)
async def setScoreForCrew(ctx: discord.ApplicationContext, crew_name: str, score: int):
    await ctx.defer(ephemeral=True)
    scoreStr = str(score)
    await main.setScore(ctx, crew_name, scoreStr)
    await ctx.send_followup("Score updated :)", ephemeral=True, delete_after=60)


@bot.slash_command(name='kick', description='Kick a member from all servers (Rising, Knowing, Racing, Servering).',
                   guild_ids=[main.risingServerId, main.racingServerId, main.knowingServerId, main.serveringServerId])
@commands.has_permissions(kick_members=True)
@discord.option(
    "user",
    description='user to kick',
    required=True,
    input_type=discord.Member
)
async def kick(ctx: discord.ApplicationContext, user: discord.Member, reason: str):
    await ctx.defer(ephemeral=True)
    await main.kickOrBanOrUnban(user, 'kick', bot, reason=reason)
    await ctx.send_followup("User kicked :)", ephemeral=True, delete_after=60)


@bot.slash_command(name='ban', description='Ban a member from all servers (Rising, Knowing, Racing, Servering).',
                   guild_ids=[main.risingServerId, main.racingServerId, main.knowingServerId, main.serveringServerId])
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
    await ctx.send_followup("User banned :)", ephemeral=True, delete_after=60)


@bot.slash_command(name='unban', description='Unban a former member from all servers.',
                   guild_ids=[main.risingServerId, main.racingServerId, main.knowingServerId, main.serveringServerId])
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
    await ctx.send_followup("User unbanned :)", ephemeral=True, delete_after=60)


@bot.slash_command(name="multiple",
                   description="Keep track of multiple accounts of the same person (same discord profile) "
                               "within the same crew",
                   guild_ids=[main.risingServerId])
@commands.has_any_role("Phoenix Family Leadership", "Fawkes Access")
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
    await ctx.send_followup(message, ephemeral=True, delete_after=5)


@bot.slash_command(name="transfer", description="Register a transfer for next season.", guild_ids=[main.risingServerId])
@commands.has_any_role("Phoenix Family Leadership", "Fawkes Access")
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
    "ping_admin",
    description="Whether or not Fawkes should ping admins for this. Check False if the admin teams were informed.",
    required=True,
    input_type=bool
)
@discord.option(
    "number_of_accounts",
    description="Number of accounts the player is moving in this transfer.",
    required=False,
    input_type=int
)
@discord.option(
    "should_kick",
    description="Whether Fawkes should kick the member. Available only if crew_to is Out of family.",
    required=False,
    input_type=bool
)
async def transfer(ctx: discord.ApplicationContext, player: discord.Member, crew_from: str, crew_to: str, season: int,
                   ping_admin: bool, number_of_accounts: int, should_kick: bool):
    await ctx.defer(ephemeral=True)
    message = await main.processTransfer(ctx, player, crew_from, crew_to, number_of_accounts, season, ping_admin,
                                         should_kick)
    await ctx.send_followup(message, ephemeral=True, delete_after=60)


@bot.slash_command(name='current_season', description="Gets the current season we're in",
                   guild_ids=[main.risingServerId])
@commands.has_role('Phoenix Rising')
async def current_season(ctx: discord.ApplicationContext):
    await ctx.send_response(str(main.getCurrentSeason()), ephemeral=True, delete_after=60)


@bot.slash_command(name="cancel_transfer", description="unregisters a transfer in case of change of plans",
                   guild_ids=[main.risingServerId])
@commands.has_any_role("Phoenix Family Leadership", "Fawkes Access")
@discord.option(
    "player",
    description="Player for which you want to unregister the transfer",
    required=True,
    input_type=discord.Member
)
@discord.option(
    "ping_admin",
    description="Whether or not Fawkes should ping admins for this. Check False if the admin teams were informed.",
    required=True,
    input_type=bool
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
async def cancel_transfer(ctx: discord.ApplicationContext, player: discord.Member, ping_admin: bool, crew_from=None,
                          crew_to=None):
    await ctx.defer(ephemeral=True)
    message = await main.unregisterTransfer(ctx, player, crew_from, crew_to, ping_admin)
    await ctx.send_followup(message, ephemeral=True, delete_after=60)


bot.run(main.discord_bot_token)
