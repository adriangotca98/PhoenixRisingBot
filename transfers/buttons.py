import discord
import main
from transfers import modals

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
