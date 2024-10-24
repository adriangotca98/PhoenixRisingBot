import discord
import main
import constants

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

class StartPushModal(discord.ui.Modal):
    def __init__(self, ctx: discord.ApplicationContext, role: discord.Role, members_channel: discord.TextChannel, chat_channel: discord.TextChannel):
        super().__init__(title=constants.commandsMessages['start_push_part_2'])
        self.ctx = ctx
        self.role = role
        self.members_channel = members_channel
        self.chat_channel = chat_channel
        self.add_item(
            discord.ui.InputText(label="Crew name", style=discord.InputTextStyle.short)
        )
    
    async def callback(self, interaction: discord.Interaction):
        if isinstance(self.children[0].value, str):
            message = main.startPush(self.role, self.members_channel, self.chat_channel, self.children[0].value)
            await interaction.response.send_message(
                message, ephemeral=True, delete_after=60
            )
        else:
            await interaction.response.send_message("Weird error...")

