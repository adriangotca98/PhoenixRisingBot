import discord
from crew.logic import RemoveCrewLogic


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
        message = await RemoveCrewLogic(self.ctx, self.crew).doWork()
        await self.ctx.send_followup(message, ephemeral=True, delete_after=60)
