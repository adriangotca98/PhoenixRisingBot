import discord
from transfers import buttons, logic
import constants
import utils


class MakeTransfersView(discord.ui.View):
    def __init__(self, ctx: discord.ApplicationContext):
        self.ctx = ctx
        super().__init__()

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def yesButtonCallback(
        self, button: discord.Button, interaction: discord.Interaction
    ):
        self.disable_all_items()
        message = await logic.makeTransfers(self.ctx)
        await interaction.response.edit_message(view=self)
        await self.ctx.send_followup(message, ephemeral=True, delete_after=60)

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def noButtonCallback(
        self, button: discord.Button, interaction: discord.Interaction
    ):
        self.disable_all_items()
        await interaction.response.edit_message(view=self)
        await self.ctx.send_followup(
            "OK, no transfers processed.", ephemeral=True, delete_after=60
        )


class TransferView(discord.ui.View):
    def __init__(self, ctx: discord.ApplicationContext):
        super().__init__()
        self.ctx = ctx
        self.user = None
        self.crew_from = None
        self.crew_to = None
        self.season = None
        self.ping = None
        self.next_buttons = None
        self.should_kick = False
        currentSeason = utils.getCurrentSeason(constants.configCollection)
        seasonOptions = []
        for i in range(5):
            seasonOptions.append(str(currentSeason + i))
        utils.resetSelect(
            self,
            {
                "crew_from": ["New to family"]
                + utils.getCrewNames(constants.configCollection),
                "crew_to": ["Out of family - kick", "Out of family - keep community"]
                + utils.getCrewNames(constants.configCollection),
                "season": seasonOptions,
            },
        )

    def maybeAddButton(self):
        if (
            self.user is not None
            and self.crew_from is not None
            and self.crew_to is not None
            and self.season is not None
        ):
            if self.next_buttons:
                for next_button in self.next_buttons:
                    self.remove_item(next_button)
            self.next_buttons = [
                buttons.TransferPingButton(
                    self.ctx,
                    self.user,
                    self.crew_from,
                    self.crew_to,
                    self.season,
                    self.should_kick,
                ),
                buttons.TransferNoPingButton(
                    self.ctx,
                    self.user,
                    self.crew_from,
                    self.crew_to,
                    self.season,
                    self.should_kick,
                ),
            ]
            for next_button in self.next_buttons:
                self.add_item(next_button)

    @discord.ui.user_select(placeholder="Select the user", row=0)
    async def userSelectCallback(
        self, select: discord.ui.Select, interaction: discord.Interaction
    ):
        if isinstance(select.values[0], discord.Member):
            self.user = select.values[0]
        self.maybeAddButton()
        await interaction.response.edit_message(view=self)

    @discord.ui.string_select(
        placeholder="Where is the player going from?", row=1, custom_id="crew_from"
    )
    async def crewFromCallback(
        self, select: discord.ui.Select, interaction: discord.Interaction
    ):
        self.crew_from = str(select.values[0])
        select = utils.updateSelect(select)
        self.maybeAddButton()
        await interaction.response.edit_message(view=self)

    @discord.ui.string_select(
        placeholder="Where is the player going to?", row=2, custom_id="crew_to"
    )
    async def crewToCallback(
        self, select: discord.ui.Select, interaction: discord.Interaction
    ):
        self.crew_to = str(select.values[0])
        if self.crew_to.endswith("kick"):
            self.should_kick = True
        if self.crew_to.startswith("Out of family"):
            self.crew_to = "Out of family"
        select = utils.updateSelect(select)
        self.maybeAddButton()
        await interaction.response.edit_message(view=self)

    @discord.ui.string_select(placeholder="Season", row=3, custom_id="season")
    async def seasonSelectCallback(
        self, select: discord.ui.Select, interaction: discord.Interaction
    ):
        self.season = int(str(select.values[0]))
        select = utils.updateSelect(select)
        self.maybeAddButton()
        await interaction.response.edit_message(view=self)


class CancelTransferView(discord.ui.View):
    def __init__(self, ctx: discord.ApplicationContext):
        super().__init__()
        self.ctx = ctx
        self.user = None
        self.crew_from = None
        self.crew_to = None
        self.next_buttons = None
        utils.resetSelect(
            self,
            {
                "crew_from": ["New to family"]
                + utils.getCrewNames(constants.configCollection),
                "crew_to": ["Out of family"]
                + utils.getCrewNames(constants.configCollection),
            },
        )

    def maybeAddButton(self):
        if (
            self.user is not None
            and self.crew_from is not None
            and self.crew_to is not None
        ):
            if self.next_buttons:
                for next_button in self.next_buttons:
                    self.remove_item(next_button)
            self.next_buttons = [
                buttons.CancelTransferPingButton(
                    self.ctx, self.user, self.crew_from, self.crew_to
                ),
                buttons.CancelTransferNoPingButton(
                    self.ctx, self.user, self.crew_from, self.crew_to
                ),
            ]
            for next_button in self.next_buttons:
                self.add_item(next_button)

    @discord.ui.user_select(placeholder="Select the user", row=0)
    async def userSelectCallback(
        self, select: discord.ui.Select, interaction: discord.Interaction
    ):
        if isinstance(select.values[0], discord.Member):
            self.user = select.values[0]
        self.maybeAddButton()
        await interaction.response.edit_message(view=self)

    @discord.ui.string_select(
        placeholder="Where is the player going from?",
        min_values=0,
        row=1,
        custom_id="crew_from",
    )
    async def crewFromCallback(
        self, select: discord.ui.Select, interaction: discord.Interaction
    ):
        self.crew_from = str(select.values[0])
        select = utils.updateSelect(select)
        self.maybeAddButton()
        await interaction.response.edit_message(view=self)

    @discord.ui.string_select(
        placeholder="Where is the player going to?",
        min_values=0,
        row=2,
        custom_id="crew_to",
    )
    async def crewToCallback(
        self, select: discord.ui.Select, interaction: discord.Interaction
    ):
        self.crew_to = str(select.values[0])
        select = utils.updateSelect(select)
        self.maybeAddButton()
        await interaction.response.edit_message(view=self)
