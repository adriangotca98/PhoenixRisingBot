import discord
import constants
from crew.logic import AddCrewLogic, EditCrewLogic
from crew import logic
import utils


class AddCrewModal(discord.ui.Modal):
    def __init__(
        self, ctx: discord.ApplicationContext, region: str, view: discord.ui.View
    ):
        super().__init__(title=constants.commandsMessages["add_crew_part_2"])
        self.ctx = ctx
        self.view = view
        self.region = region
        self.shortname: str | None = None
        self.longname: str | None = None
        self.add_item(
            discord.ui.InputText(label="Short name", style=discord.InputTextStyle.short)
        )
        self.add_item(
            discord.ui.InputText(label="Long name", style=discord.InputTextStyle.short)
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(view=self.view)
        if isinstance(self.children[0].value, str) and isinstance(
            self.children[1].value, str
        ):
            self.shortname = self.children[0].value
            self.longname = self.children[1].value
            try:
                message = await AddCrewLogic(
                    self.ctx, self.region, self.shortname, self.longname
                ).doWork()
            except (ValueError, RuntimeError) as e:
                message = str(e)
        else:
            message = None
        await self.ctx.send_followup(message, ephemeral=True, delete_after=60)


class EditCrewModal(discord.ui.Modal):
    def __init__(
        self,
        ctx: discord.ApplicationContext,
        crew: str,
        fieldToEdit: str,
        view: discord.ui.View,
    ):
        oldValue = utils.getCrewField(crew, fieldToEdit)
        super().__init__(
            title=constants.commandsMessages["edit_crew_part_2"](fieldToEdit)
        )
        self.ctx = ctx
        self.view = view
        self.crew = crew
        self.fieldToEdit = fieldToEdit
        self.newValue: str | None = None
        self.add_item(
            discord.ui.InputText(
                label=f'Old value was "{oldValue}"', style=discord.InputTextStyle.short
            )
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(view=self.view)
        if isinstance(self.children[0].value, str):
            self.newValue = self.children[0].value
            try:
                message = await EditCrewLogic(
                    self.ctx, self.crew, self.fieldToEdit, self.newValue
                ).doWork()
            except ValueError as e:
                message = str(e)
        else:
            message = None
        await self.ctx.send_followup(message, ephemeral=True, delete_after=60)
