import discord
import constants
from members.views import KickBanUnbanView, MembersCrewsView, MultipleView
from transfers.views import CancelTransferView, MakeTransfersView, TransferView
from score.views import ScoreView
import utils


class FawkesView(discord.ui.View):
    def __init__(self, ctx: discord.ApplicationContext, bot: discord.Bot):
        self.ctx = ctx
        self.bot = bot
        super().__init__()
        utils.resetSelect(self, {"operation": constants.commandsList})

    @discord.ui.select(
        placeholder="Pick an operation to be performed by Fawkes",
        options=list(
            map(lambda name: discord.SelectOption(label=name), constants.commandsList)
        ),
        custom_id="operation",
    )
    async def selectCallback(
        self, select: discord.ui.Select, interaction: discord.Interaction
    ):
        views = {
            "ban": KickBanUnbanView(self.ctx, self.bot, "ban"),
            "cancel_transfer": CancelTransferView(self.ctx),
            "kick": KickBanUnbanView(self.ctx, self.bot, "kick"),
            "members": MembersCrewsView(self.ctx),
            "make_transfers": MakeTransfersView(self.ctx),
            "multiple": MultipleView(self.ctx),
            "score": ScoreView(self.ctx),
            "transfer": TransferView(self.ctx),
            "unban": KickBanUnbanView(self.ctx, self.bot, "unban"),
        }
        message = constants.commandsMessages[str(select.values[0])]
        if select.values[0] not in views.keys():
            await interaction.response.send_message(
                message, ephemeral=True, delete_after=60
            )
        else:
            view = views[str(select.values[0])]
            await interaction.response.send_message(
                message, view=view, ephemeral=True, delete_after=600
            )
