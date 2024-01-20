import discord
from discord.interactions import Interaction
import main

class ScoreModal(discord.ui.Modal):
    def __init__(self, ctx: discord.ApplicationContext, crew: str):
        super().__init__(title='Enter the score for {crew}.')
        self.ctx = ctx
        self.crew = crew
        self.add_item(discord.ui.InputText(label="Score", style=discord.InputTextStyle.short))
    
    async def callback(self, interaction: Interaction):
        try:
            score = int(self.children[0].value)
            await main.setScore(self.ctx, self.crew, score)
            await interaction.response.send_message("Score updated.", ephemeral=True, delete_after=60)
        except ValueError:
            await interaction.response.send_message("Errored out cause the number given was not a number, try again with a number.", ephemeral=True, delete_after=60)