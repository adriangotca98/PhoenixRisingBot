import discord
import modals
import main

from discord.interactions import Interaction

class MultipleButton(discord.ui.Button):
    def __init__(self, ctx: discord.ApplicationContext, player: discord.Member, crew: str, number: int):
        super().__init__()
        self.row=3
        self.ctx=ctx
        self.player=player
        self.crew=crew
        self.number=number
        self.label="Submit!"
        self.style=discord.ButtonStyle.green
    
    async def callback(self, interaction: discord.Interaction):
        print(self.view.crew)
        print(self.view.number)
        print(self.view.player)
        self.view.disable_all_items()
        await interaction.response.edit_message(view=self.view)  
        message = main.processMultiple(self.player, self.crew, self.number)
        await self.ctx.send_followup(message, ephemeral=True, delete_after=60)

class ScoreNextButton(discord.ui.Button):
    def __init__(self, ctx: discord.ApplicationContext, crew: str):
        super().__init__()
        self.row=1
        self.ctx=ctx
        self.crew = crew
        self.label="Next"
        self.style=discord.ButtonStyle.blurple
    
    async def callback(self, interaction: Interaction):
        await interaction.response.send_modal(modals.ScoreModal(self.ctx, self.crew))