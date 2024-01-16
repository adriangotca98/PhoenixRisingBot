import discord
import main

class MembersCrewsView(discord.ui.View):
    def __init__(self, ctx: discord.ApplicationContext):
        self.ctx = ctx
        super().__init__()

    @discord.ui.select(
        placeholder="Pick a crew to update members for!",
        min_values=1,
        max_values=1,
        options=list(map(lambda name: discord.SelectOption(label=name), main.getCrewNames()))
    )

    async def select_callback(self, select, interaction: discord.Interaction):
        select.disabled = True
        await interaction.response.edit_message(view=self)
        message = await main.getPlayersResponse(self.ctx, select.values[0])
        await self.ctx.send_followup(message, ephemeral=True, delete_after=60)