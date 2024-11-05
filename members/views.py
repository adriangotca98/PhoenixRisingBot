import discord
import utils
import constants
from members import buttons, logic
import utils


class MembersCrewsView(discord.ui.View):
    def __init__(self, ctx: discord.ApplicationContext):
        self.ctx = ctx
        super().__init__()
        utils.resetSelect(
            self, {"crew": utils.getCrewNames(constants.configCollection)}
        )

    @discord.ui.select(
        placeholder="Pick a crew to update members for!", custom_id="crew"
    )
    async def selectCallback(
        self, select: discord.ui.Select, interaction: discord.Interaction
    ):
        select.disabled = True
        await interaction.response.edit_message(view=self)
        message = await logic.getPlayersResponse(self.ctx, str(select.values[0]))
        await self.ctx.send_followup(message, ephemeral=True, delete_after=60)


class MultipleView(discord.ui.View):
    def __init__(self, ctx: discord.ApplicationContext):
        self.ctx = ctx
        self.player = None
        self.crew = None
        self.number = None
        self.has_button = False
        super().__init__()
        utils.resetSelect(
            self,
            {
                "crew": utils.getCrewNames(constants.configCollection),
                "number_of_accounts": list(range(1, 11)),
            },
        )

    def maybeAddButton(self):
        if (
            self.player is not None
            and self.crew is not None
            and self.number is not None
            and self.has_button is False
        ):
            self.has_button = True
            self.add_item(
                buttons.MultipleButton(self.ctx, self.player, self.crew, self.number)
            )

    @discord.ui.user_select(placeholder="Choose a player", row=0)
    async def userSelectCallback(
        self, select: discord.ui.Select, interaction: discord.Interaction
    ):
        if isinstance(select.values[0], discord.Member):
            self.player = select.values[0]
        self.maybeAddButton()
        await interaction.response.edit_message(view=self)

    @discord.ui.select(
        placeholder="Choose the crew where the player has more than 1 account!",
        row=1,
        custom_id="crew",
    )
    async def crewSelectCallback(
        self, select: discord.ui.Select, interaction: discord.Interaction
    ):
        self.crew = str(select.values[0])
        select = utils.updateSelect(select)
        self.maybeAddButton()
        await interaction.response.edit_message(view=self)

    @discord.ui.string_select(
        placeholder="Choose the number of accounts the player has in the crew.",
        row=2,
        custom_id="number_of_accounts",
    )
    async def inputCallback(
        self, select: discord.ui.Select, interaction: discord.Interaction
    ):
        self.number = int(str(select.values[0]))
        select = utils.updateSelect(select)
        self.maybeAddButton()
        await interaction.response.edit_message(view=self)


class KickBanUnbanView(discord.ui.View):
    def __init__(self, ctx: discord.ApplicationContext, bot: discord.Bot, op: str):
        super().__init__()
        self.ctx = ctx
        self.bot = bot
        self.op = op

    @discord.ui.user_select(placeholder="Select the user", row=0)
    async def callback(
        self, select: discord.ui.Select, interaction: discord.Interaction
    ):
        member = select.values[0]
        if isinstance(member, discord.Member):
            self.add_item(
                buttons.KickBanUnbanButton(self.ctx, self.bot, self.op, member)
            )
        await interaction.response.edit_message(view=self)
