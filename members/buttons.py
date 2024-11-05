import discord
from members import modals
import logic

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
        message = logic.processMultiple(self.player, self.crew, self.number)
        await self.ctx.send_followup(message, ephemeral=True, delete_after=60)

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
            await logic.kickOrBanOrUnban(self.user, self.op, self.bot)
        else:
            await interaction.response.send_modal(
                modals.KickBanModal(self.user, self.op, self.bot)
            )
