import discord
from score import modals

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
