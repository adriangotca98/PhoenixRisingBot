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
        for child in self.children:
            if isinstance(child, discord.ui.Select):
                child.options = list(
                    map(
                        lambda name: discord.SelectOption(label=name, default=False),
                        ["EU", "US", "AUS/JPN"],
                    )
                )

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
        for child in self.children:
            if isinstance(child, discord.ui.Select):
                child.options = list(
                    map(
                        lambda name: discord.SelectOption(label=name, default=False),
                        utils.getCrewNames(constants.configCollection),
                    )
                )

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
