import discord
import utils
from push import modals
import constants
import logic

class EndPushView(discord.ui.View):
    def __init__(self, ctx: discord.ApplicationContext):
        super().__init__()
        self.ctx = ctx
        self.crew_name = None
        for child in self.children:
            if isinstance(child, discord.ui.Select):
                child.options = list(
                    map(
                        lambda name: discord.SelectOption(label=name, default=False),
                        utils.getPushCrewNames(constants.configCollection),
                    )
                )

    @discord.ui.string_select(placeholder="Push crew")
    async def callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        if isinstance(select.values[0], str):
            message = logic.endPush(select.values[0])
            await interaction.response.send_message(message, ephemeral=True, delete_after=60)


class StartPushView(discord.ui.View):
    def __init__(self, ctx: discord.ApplicationContext):
        super().__init__()
        self.ctx = ctx
        self.role = None
        self.members_channel = None
        self.chat_channel = None

    async def maybeSendModal(self, interaction: discord.Interaction):
        if self.role is not None and self.members_channel is not None and self.chat_channel is not None:
            await interaction.response.send_modal(modals.StartPushModal(self.ctx, self.role, self.members_channel, self.chat_channel))
        else:
            await interaction.response.edit_message(view=self)

    @discord.ui.role_select(
        placeholder="Choose the role for the Top 10 push crew",
    )
    async def roleSelectCallback(self, select: discord.ui.Select, interaction: discord.Interaction):
        if isinstance(select.values[0], discord.Role):
            self.role = select.values[0]
        await self.maybeSendModal(interaction)
    
    @discord.ui.channel_select(
        placeholder='Choose the members channel for the members list',
    )
    async def membersChannelSelectCallback(self, select: discord.ui.Select, interaction: discord.Interaction):
        if isinstance(select.values[0], discord.TextChannel):
            self.members_channel = select.values[0]
        await self.maybeSendModal(interaction)
    
    @discord.ui.channel_select(
        placeholder='Choose the chat channel',
    )
    async def chatChannelSelectCallback(self, select: discord.ui.Select, interaction: discord.Interaction):
        if isinstance(select.values[0], discord.TextChannel):
            self.chat_channel = select.values[0]
        await self.maybeSendModal(interaction)
