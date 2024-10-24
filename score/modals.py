import discord
import main

class ScoreModal(discord.ui.Modal):
    def __init__(self, ctx: discord.ApplicationContext, crew: str):
        super().__init__(title="Enter the score for {crew}.")
        self.ctx = ctx
        self.crew = crew
        self.add_item(
            discord.ui.InputText(label="Score", style=discord.InputTextStyle.short)
        )

    async def callback(self, interaction: discord.Interaction):
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
