import discord
from crew import modals
import constants
import utils
from crew import buttons

class AddCrewView(discord.ui.View):
    def __init__(self, ctx: discord.ApplicationContext):
        super().__init__()
        self.ctx = ctx
        self.region = None
        utils.resetSelect(self, ['EU','US','AUS/JPN'], constants.availableFieldsToEditInCrew)

    async def maybeSendModal(self, interaction: discord.Interaction):
        if self.region is not None:
            await interaction.response.send_modal(
                modals.AddCrewModal(self.ctx, self.region, self)
            )
        else:
            await interaction.response.edit_message(view=self)

    @discord.ui.string_select(placeholder="Region")
    async def regionSelectCallback(
        self, select: discord.ui.Select, interaction: discord.Interaction
    ):
        if isinstance(select.values[0], str):
            self.region = select.values[0]
        select = utils.updateSelect(select)
        await self.maybeSendModal(interaction)

class RemoveCrewView(discord.ui.View):
    def __init__(self, ctx: discord.ApplicationContext):
        super().__init__()
        self.ctx = ctx
        self.crew = None
        utils.resetSelect(self, utils.getCrewNames(constants.configCollection))

    def maybeAddButton(self):
        if isinstance(self.crew, str):
            self.add_item(buttons.RemoveCrewButton(self.ctx, self.crew))

    @discord.ui.string_select(placeholder="Crew to delete")
    async def crewSelectCallback(
        self, select: discord.ui.Select, interaction: discord.Interaction
    ):
        self.crew = select.values[0]
        select = utils.updateSelect(select)
        self.maybeAddButton()
        await interaction.response.edit_message(view=self)

class EditCrewView(discord.ui.View):
    def __init__(self, ctx: discord.ApplicationContext):
        self.ctx = ctx
        self.crew = None
        self.fieldToEdit = None
        utils.resetSelect(self, utils.getCrewNames(constants.configCollection))

    @discord.ui.string_select(placeholder="Crew to edit")
    async def crewSelectCallback(
        self, select: discord.ui.Select, interaction: discord.Interaction
    ):
        self.crew = select.values[0]
        select = utils.updateSelect(select)
        await self.maybeSendModal(interaction)

    @discord.ui.string_select(placeholder="Field to edit")
    async def fieldToEditSelectCallback(
        self, select: discord.ui.Select, interaction: discord.Interaction
    ):
        self.fieldToEdit = select.values[0]
        select = utils.updateSelect(select)
        await self.maybeSendModal(interaction)

    async def maybeSendModal(self, interaction: discord.Interaction):
        if isinstance(self.fieldToEdit, str) and isinstance(self.crew, str):
            await interaction.response.send_modal(
                modals.EditCrewModal(self.ctx, self.crew, self.fieldToEdit, self)
            )
        else:
            await interaction.response.edit_message(view=self)
