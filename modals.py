import discord
from discord.interactions import Interaction
import main
import constants


class ScoreModal(discord.ui.Modal):
    def __init__(self, ctx: discord.ApplicationContext, crew: str):
        super().__init__(title="Enter the score for {crew}.")
        self.ctx = ctx
        self.crew = crew
        self.add_item(
            discord.ui.InputText(label="Score", style=discord.InputTextStyle.short)
        )

    async def callback(self, interaction: Interaction):
        try:
            score = int(str(self.children[0].value))
            await main.setScore(self.ctx, self.crew, str(score))
            await interaction.response.send_message(
                "Score updated.", ephemeral=True, delete_after=60
            )
        except ValueError:
            await interaction.response.send_message(
                "Error out cause the number given was not a number, try again with a number.",
                ephemeral=True,
                delete_after=60,
            )


class StartPushModal(discord.ui.Modal):
    def __init__(self, ctx: discord.ApplicationContext, role: discord.Role, members_channel: discord.TextChannel, chat_channel: discord.TextChannel):
        super().__init__(title=constants.commandsMessages['start_push_part_2'])
        self.ctx = ctx
        self.role = role
        self.members_channel = members_channel
        self.chat_channel = chat_channel
        self.add_item(
            discord.ui.InputText(label="Crew name", style=discord.InputTextStyle.short)
        )
    
    async def callback(self, interaction: discord.Interaction):
        if isinstance(self.children[0].value, str):
            message = main.startPush(self.role, self.members_channel, self.chat_channel, self.children[0].value)
            await interaction.response.send_message(
                message, ephemeral=True, delete_after=60
            )
        else:
            await interaction.response.send_message("Weird error...")


class KickBanModal(discord.ui.Modal):
    def __init__(self, user, op, bot):
        super().__init__(title=f"Enter the reason, if any for the {op}")
        self.user = user
        self.op = op
        self.bot = bot
        self.add_item(
            discord.ui.InputText(label="Reason", style=discord.InputTextStyle.short)
        )

    async def callback(self, interaction: Interaction):
        await main.kickOrBanOrUnban(
            self.user, self.op, self.bot, self.children[0].value
        )
        message = "User kicked." if self.op == "kick" else "User banned."
        await interaction.response.send_message(
            message, ephemeral=True, delete_after=60
        )


class TransferModal(discord.ui.Modal):
    def __init__(
        self,
        ctx: discord.ApplicationContext,
        view: discord.ui.View,
        user: discord.Member,
        crew_from: str,
        crew_to: str,
        season: int,
        ping: bool,
        should_kick: bool,
    ):
        super().__init__(title="Transfer, part 2")
        self.ctx = ctx
        self.view = view
        self.user = user
        self.crew_from = crew_from
        self.crew_to = crew_to
        self.season = season
        self.ping = ping
        self.should_kick = should_kick
        self.add_item(
            discord.ui.InputText(
                label="Number of accounts",
                style=discord.InputTextStyle.short,
                required=False,
            )
        )

    async def callback(self, interaction: discord.Interaction):
        number_of_accounts = -1
        try:
            number_of_accounts = int(str(self.children[0].value))
        except ValueError:
            number_of_accounts = 1
        finally:
            await interaction.response.edit_message(view=self.view)
            message = await main.processTransfer(
                self.ctx,
                self.user,
                self.crew_from,
                self.crew_to,
                number_of_accounts,
                self.season,
                self.ping,
                self.should_kick,
            )
            await self.ctx.send_followup(message, ephemeral=True, delete_after=60)


class AddCrewModal(discord.ui.Modal):
    def __init__(
        self, ctx: discord.ApplicationContext, region: str, view: discord.ui.View
    ):
        super().__init__(title=constants.commandsMessages["add_crew_part_2"])
        self.ctx = ctx
        self.view = view
        self.region = region
        self.shortname: str | None = None
        self.add_item(
            discord.ui.InputText(label="Short name", style=discord.InputTextStyle.short)
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(view=self.view)
        if isinstance(self.children[0].value, str):
            self.shortname = self.children[0].value
            message = await main.addCrew(self.ctx, self.region, self.shortname)
        else:
            message = None
        await self.ctx.send_followup(message, ephemeral=True, delete_after=60)
