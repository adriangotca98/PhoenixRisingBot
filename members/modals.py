import discord
import logic

class KickBanModal(discord.ui.Modal):
    def __init__(self, user, op, bot):
        super().__init__(title=f"Enter the reason, if any for the {op}")
        self.user = user
        self.op = op
        self.bot = bot
        self.add_item(
            discord.ui.InputText(label="Reason", style=discord.InputTextStyle.short)
        )

    async def callback(self, interaction: discord.Interaction):
        await logic.kickOrBanOrUnban(
            self.user, self.op, self.bot, self.children[0].value
        )
        message = "User kicked." if self.op == "kick" else "User banned."
        await interaction.response.send_message(
            message, ephemeral=True, delete_after=60
        )
