import discord
import modals
import main


class MultipleButton(discord.ui.Button):
    def __init__(
        self,
        ctx: discord.ApplicationContext,
        player: discord.Member,
        crew: str,
        number: int,
    ):
        super().__init__()
        self.row = 3
        self.ctx = ctx
        self.player = player
        self.crew = crew
        self.number = number
        self.label = "Submit!"
        self.style = discord.ButtonStyle.green

    async def callback(self, interaction: discord.Interaction):
        if isinstance(self.view, discord.ui.View):
            self.view.disable_all_items()
        await interaction.response.edit_message(view=self.view)
        message = main.processMultiple(self.player, self.crew, self.number)
        await self.ctx.send_followup(message, ephemeral=True, delete_after=60)


class ScoreNextButton(discord.ui.Button):
    def __init__(self, ctx: discord.ApplicationContext, crew: str):
        super().__init__()
        self.row = 1
        self.ctx = ctx
        self.crew = crew
        self.label = "Next"
        self.style = discord.ButtonStyle.blurple

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(modals.ScoreModal(self.ctx, self.crew))


class KickBanUnbanButton(discord.ui.Button):
    def __init__(
        self,
        ctx: discord.ApplicationContext,
        bot: discord.Bot,
        op: str,
        user: discord.Member,
    ):
        super().__init__()
        self.ctx = ctx
        self.label = op
        self.op = op
        self.user = user
        self.bot = bot
        self.style = (
            discord.ButtonStyle.green if op == "unban" else discord.ButtonStyle.blurple
        )

    async def callback(self, interaction: discord.Interaction):
        if self.op == "unban":
            await main.kickOrBanOrUnban(self.user, self.op, self.bot)
        else:
            await interaction.response.send_modal(
                modals.KickBanModal(self.user, self.op, self.bot)
            )


class CancelTransferPingButton(discord.ui.Button):
    def __init__(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Member,
        crew_from: str,
        crew_to: str,
    ):
        super().__init__()
        self.label = "Send with ping to admins!"
        self.style = discord.ButtonStyle.green
        self.ctx = ctx
        self.user = user
        self.crew_from = crew_from
        self.crew_to = crew_to
        self.ping = True

    async def callback(self, interaction: discord.Interaction):
        if isinstance(self.view, discord.ui.View):
            self.view.disable_all_items()
        await interaction.response.edit_message(view=self.view)
        message = await main.unregisterTransfer(
            self.ctx, self.user, self.crew_from, self.crew_to, self.ping
        )
        await self.ctx.send_followup(message, ephemeral=True, delete_after=60)


class CancelTransferNoPingButton(CancelTransferPingButton):
    def __init__(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Member,
        crew_from: str,
        crew_to: str,
    ):
        super().__init__(ctx, user, crew_from, crew_to)
        self.ping = False
        self.label = "Send with no ping to admins!"
        self.style = discord.ButtonStyle.red


class TransferNoPingButton(CancelTransferNoPingButton):
    def __init__(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Member,
        crew_from: str,
        crew_to: str,
        season: int,
        should_kick: bool,
    ):
        super().__init__(ctx, user, crew_from, crew_to)
        self.season = season
        self.should_kick = should_kick

    async def callback(self, interaction: discord.Interaction):
        if isinstance(self.view, discord.ui.View):
            self.view.disable_all_items()
            await interaction.response.send_modal(
                modals.TransferModal(
                    self.ctx,
                    self.view,
                    self.user,
                    self.crew_from,
                    self.crew_to,
                    self.season,
                    self.ping,
                    self.should_kick,
                )
            )


class TransferPingButton(TransferNoPingButton):
    def __init__(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Member,
        crew_from: str,
        crew_to: str,
        season: int,
        should_kick: bool,
    ):
        super().__init__(ctx, user, crew_from, crew_to, season, should_kick)
        self.ping = True
        self.label = "Send with ping to admins!"
        self.style = discord.ButtonStyle.green


class RemoveCrewButton(discord.ui.Button):
    def __init__(self, ctx: discord.ApplicationContext, crew: str):
        super().__init__()
        self.style = discord.ButtonStyle.red
        self.label = f"I'm sure, delete {crew.upper()}!"
        self.ctx = ctx
        self.crew = crew

    async def callback(self, interaction: discord.Interaction):
        if self.view:
            self.view.disable_all_items()
        await interaction.response.edit_message(view=self.view)
        message = await main.removeCrew(self.ctx, self.crew)
        await self.ctx.send_followup(message, ephemeral=True, delete_after=60)
