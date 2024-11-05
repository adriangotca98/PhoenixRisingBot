import discord
from push import logic
import constants


class StartPushModal(discord.ui.Modal):
    def __init__(
        self,
        ctx: discord.ApplicationContext,
        role: discord.Role,
        members_channel: discord.TextChannel,
        chat_channel: discord.TextChannel,
    ):
        super().__init__(title=constants.commandsMessages["start_push_part_2"])
        self.ctx = ctx
        self.role = role
        self.members_channel = members_channel
        self.chat_channel = chat_channel
        self.add_item(
            discord.ui.InputText(label="Crew name", style=discord.InputTextStyle.short)
        )

    async def callback(self, interaction: discord.Interaction):
        if isinstance(self.children[0].value, str):
            message = logic.startPush(
                self.role,
                self.members_channel,
                self.chat_channel,
                self.children[0].value,
            )
            await interaction.response.send_message(
                message, ephemeral=True, delete_after=60
            )
        else:
            await interaction.response.send_message("Weird error...")
