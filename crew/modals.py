import discord
import constants
import main

class AddCrewModal(discord.ui.Modal):
    def __init__(
        self, ctx: discord.ApplicationContext, region: str, view: discord.ui.View
    ):
        super().__init__(title=constants.commandsMessages["add_crew_part_2"])
        self.ctx = ctx
        self.view = view
        self.region = region
        self.shortname: str | None = None
        self.add_item(
            discord.ui.InputText(label="Short name", style=discord.InputTextStyle.short)
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(view=self.view)
        if isinstance(self.children[0].value, str):
            self.shortname = self.children[0].value
            message = await main.addCrew(self.ctx, self.region, self.shortname)
        else:
            message = None
        await self.ctx.send_followup(message, ephemeral=True, delete_after=60)
