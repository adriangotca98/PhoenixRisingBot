import discord
import logic

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
            message = await logic.processTransfer(
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

