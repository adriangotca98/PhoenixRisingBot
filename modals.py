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

class KickBanModal(discord.ui.Modal):
    def __init__(self, user, op, bot):
        super.__init__(title=f"Enter the reason, if any for the {op}")
        self.user = user
        self.op = op
        self.bot = bot
        self.add_item(discord.ui.InputText(label="Reason", style=discord.InputTextStyle.short))
    
    async def callback(self, interaction: Interaction):
        await main.kickOrBanOrUnban(self.user, self.op, self.bot, self.children[0].value)
        message = "User kicked." if self.op == "kick" else "User banned."
        await interaction.response.send_message(message, ephemeral = True, delete_after=60)