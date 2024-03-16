import discord
from discord.ext import commands
import main
import constants
import views

description = """Phoenix Rising family bot, Fawkes."""

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = discord.Bot(description=description, intents=intents)


@bot.event
async def on_ready():
    await main.init(bot)
    print(f"Logged in as {bot.user} (ID: {bot.user.id if bot.user is not None else 0})")
    print("------")


async def getOptionStr(ctx: discord.ApplicationContext, option):
    try:
        value = option["value"]
        member_id = int(value)
        member = await ctx.bot.fetch_user(member_id)
        if member.discriminator != 0:
            return f"{member.name}#{member.discriminator}"
        return f"{member.name}"
    except (
        discord.errors.Forbidden,
        discord.errors.HTTPException,
        discord.errors.NotFound,
    ):
        return str(option["value"])
    except ValueError:
        return str(option["value"])


@bot.event
async def on_application_command_completion(ctx: discord.ApplicationContext):
    args = ""
    if ctx.selected_options is not None:
        for option in ctx.selected_options:
            option_str = await getOptionStr(ctx, option) + " "
            args += option_str
    if ctx.author is not None:
        discriminator = (
            f"#{ctx.author.discriminator}" if ctx.author.discriminator != "0" else ""
        )
        message = (
            f"**{ctx.author.name}{discriminator}** has sent the following command:"
            f"**/{ctx.command.name} {args}**"
        )
        channel = await bot.fetch_channel(constants.loggingChannelId)
        if isinstance(channel, discord.TextChannel):
            await channel.send(message)


@bot.event
async def on_application_command_error(ctx: discord.ApplicationContext, error):
    if isinstance(error, commands.MissingRole) or isinstance(
        error, commands.MissingPermissions
    ):
        if ctx.author is not None:
            await ctx.send_response(
                "<@"
                + str(ctx.author.id)
                + ">, you're not authorized to use this command! Only leadership can use this. Thank "
                "you :) ",
                ephemeral=True,
            )
        return
    await ctx.send(
        f"An unexpected error has occurred. <@308561593858392065>, please have a look in the code. "
        f"Command run: {ctx.command.name}"
    )
    args = None
    if ctx.selected_options is not None:
        args = " ".join(
            [(await getOptionStr(ctx, option)) for option in ctx.selected_options]
        )
    if ctx.author is not None:
        discriminator = (
            f"#{ctx.author.discriminator}" if ctx.author.discriminator != "0" else ""
        )
        message = (
            f"**{ctx.author.name}{discriminator}** tried to send the following command: "
            f"**/{ctx.command.name} {args}**, but it error out."
        )
        channel = await bot.fetch_channel(constants.loggingChannelId)
        if isinstance(channel, discord.TextChannel):
            await channel.send(message)
    try:
        await ctx.send_followup(f"Failed unexpectedly", ephemeral=True)
    except RuntimeError:
        await ctx.send("Failed unexpectedly")
    raise error


@bot.slash_command(
    name='start_push',
    description='Starts a push tracking in Fawkes.',
    guild_ids=[constants.risingServerId]
)
@commands.has_any_role("Server Moderator")
async def startPush(ctx: discord.ApplicationContext):
    await ctx.send_response(
        constants.commandsMessages['start_push_part_1'],
        views=views.StartPushView(ctx),
        ephemeral=True,
        delete_after=600
    )


@bot.slash_command(
    name='end_push',
    description='Ends a push tracking for a push crew in Fawkes.',
    guild_ids=[constants.risingServerId]
)
@commands.has_any_role("Server Moderator")
async def endPush(ctx: discord.ApplicationContext):
    await ctx.send_response(
        constants.commandsMessages['end_push'],
        views=views.EndPushView(ctx),
        ephemeral=True,
        delete_after=600
    )


@bot.slash_command(
    name="add_crew",
    description="Used to add another crew to Fawkes tracking",
    guild_ids=[constants.risingServerId],
)
@commands.has_any_role("Server Moderator")
async def addCrew(ctx: discord.ApplicationContext):
    await ctx.send_response(
        constants.commandsMessages["add_crew_part_1"],
        view=views.AddCrewView(ctx),
        ephemeral=True,
        delete_after=600,
    )


@bot.slash_command(
    name="remove_crew",
    description="Used to remove a crew from Fawkes DB, as well as delete channels and roles related to it.",
    guild_ids=[constants.risingServerId],
)
@commands.has_any_role("Server Moderator")
async def removeCrew(ctx: discord.ApplicationContext):
    await ctx.send_response(
        constants.commandsMessages["remove_crew"],
        view=views.RemoveCrewView(ctx),
        ephemeral=True,
        delete_after=600,
    )


@bot.slash_command(
    name="fawkes",
    description="Gets all the commands Fawkes is able to run and a dropdown to select what you want to run",
    guild_ids=[constants.risingServerId],
)
@commands.has_any_role("Phoenix Family Leadership", "Fawkes Access")
async def fawkes(ctx: discord.ApplicationContext):
    message = """
**COMMANDS THAT FAWKES KNOWS: **
- **ban**: bans someone from the server
- **cancel_transfer**: cancels an already registeres transfer
- **current_season**: shows the season we're currently in
- **kick**: kicks someone from the server
- **make_transfers**: makes all the transfers in a season manually (gives roles, removes old roles, kicks if necessary)
- **members**: refreshes the members list with the newly added transfers or canceled transfers
- **multiple**: registers someone with a single account in Discord but multiple accounts in a single crew.
- **score**: updates the leaderboard of the crew with the score given as input
- **transfer**: register a transfer of a player either new to family, or out of family or between crews
- **unban**: unbans someone from the server
"""
    await ctx.send_response(
        message, ephemeral=True, delete_after=600, view=views.FawkesView(ctx, bot)
    )


@bot.slash_command(
    name="members",
    description="Refresh the members list for a given crew",
    guild_ids=[constants.risingServerId],
)
@commands.has_any_role("Phoenix Family Leadership", "Fawkes Access")
async def members(ctx: discord.ApplicationContext):
    await ctx.send_response(
        constants.commandsMessages["members"],
        view=views.MembersCrewsView(ctx),
        ephemeral=True,
        delete_after=600,
    )


@bot.slash_command(
    name="multiple",
    description="Register a player with multiple accounts in a single crew",
    guild_ids=[constants.risingServerId],
)
@commands.has_any_role("Phoenix Family Leadership", "Fawkes Access")
async def multiple(ctx: discord.ApplicationContext):
    await ctx.send_response(
        constants.commandsMessages["multiple"],
        view=views.MultipleView(ctx),
        ephemeral=True,
        delete_after=600,
    )


@bot.slash_command(
    name="score",
    description="Sets a score for the crew given",
    guild_ids=[constants.risingServerId],
)
@commands.has_any_role("Phoenix Family Leadership", "Fawkes Access")
async def score(ctx: discord.ApplicationContext):
    await ctx.send_response(
        constants.commandsMessages["score"],
        view=views.ScoreView(ctx),
        ephemeral=True,
        delete_after=600,
    )


@bot.slash_command(name="ban", description="Bans a user")
@commands.has_permissions(ban_members=True)
async def ban(ctx: discord.ApplicationContext):
    await ctx.send_response(
        constants.commandsMessages["ban"],
        view=views.KickBanUnbanView(ctx, bot, "ban"),
        ephemeral=True,
        delete_after=600,
    )


@bot.slash_command(name="unban", description="Unbans a user")
@commands.has_permissions(ban_members=True)
async def unban(ctx: discord.ApplicationContext):
    await ctx.send_response(
        constants.commandsMessages["unban"],
        view=views.KickBanUnbanView(ctx, bot, "unban"),
        ephemeral=True,
        delete_after=600,
    )


@bot.slash_command(name="kick", description="Kicks a user")
@commands.has_permissions(kick_members=True)
async def kick(ctx: discord.ApplicationContext):
    await ctx.send_response(
        constants.commandsMessages["kick"],
        view=views.KickBanUnbanView(ctx, bot, "kick"),
        ephemeral=True,
        delete_after=600,
    )


@bot.slash_command(name="transfer", description="Used to register a transfer")
@commands.has_any_role("Phoenix Family Leadership", "Fawkes Access")
async def transfer(ctx: discord.ApplicationContext):
    await ctx.send_response(
        constants.commandsMessages["transfer"](),
        view=views.TransferView(ctx),
        ephemeral=True,
        delete_after=600,
    )


@bot.slash_command(name="cancel_transfer", description="Used to cancel a transfer")
@commands.has_any_role("Phoenix Family Leadership", "Fawkes Access")
async def cancelTransfer(ctx: discord.ApplicationContext):
    await ctx.send_response(
        constants.commandsMessages["cancel_transfer"],
        view=views.CancelTransferView(ctx),
        ephemeral=True,
        delete_after=600,
    )


@bot.slash_command(
    name="make_transfers",
    description="Used to process all transfers from last season or a given season.",
    guild_ids=[constants.risingServerId],
)
@commands.has_any_role("Phoenix Family Leadership", "Fawkes Access")
async def makeTransfers(ctx: discord.ApplicationContext):
    await ctx.defer(ephemeral=True)
    message = await main.makeTransfers(ctx)
    await ctx.send_followup(message, ephemeral=True, delete_after=60)


@bot.slash_command(
    name="current_season",
    description="Gets the current season we're in",
    guild_ids=[constants.risingServerId],
)
@commands.has_role("Phoenix Rising")
async def current_season(ctx: discord.ApplicationContext):
    await ctx.send_response(
        constants.commandsMessages["current_season"](), ephemeral=True, delete_after=60
    )


bot.run(constants.discord_bot_token)
