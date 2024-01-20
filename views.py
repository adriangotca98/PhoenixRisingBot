import discord
from discord.interactions import Interaction
import main
import buttons

def updateSelect(select: discord.ui.Select):
    for idx in range(len(select.options)):
        select.options[idx].default = False
        if select.options[idx].label == select.values[0]:
            select.options[idx].default = True
    return select

class MembersCrewsView(discord.ui.View):
    def __init__(self, ctx: discord.ApplicationContext):
        self.ctx = ctx
        super().__init__()

    @discord.ui.select(
        placeholder="Pick a crew to update members for!",
        options=list(map(lambda name: discord.SelectOption(label=name), main.getCrewNames()))
    )
    async def select_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        select.disabled = True
        await interaction.response.edit_message(view=self)
        message = await main.getPlayersResponse(self.ctx, select.values[0])
        await self.ctx.send_followup(message, ephemeral=True, delete_after=60)

class MultipleView(discord.ui.View):
    def __init__(self, ctx: discord.ApplicationContext):
        self.ctx=ctx
        self.player=None
        self.crew=None
        self.number=None
        self.has_button=False
        super().__init__()

    def maybe_add_button(self):
        if self.player is not None and self.crew is not None and self.number is not None and self.has_button == False:
            self.has_button = True
            self.add_item(buttons.MultipleButton(self.ctx, self.player, self.crew, self.number))

    @discord.ui.user_select(
        placeholder="Choose a player",
        row=0
    )
    async def user_select_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        self.player=select.values[0]
        print(select.values[0].mention)
        self.maybe_add_button()
        await interaction.response.edit_message(view=self)

    @discord.ui.select(
        placeholder="Choose the crew where the player has more than 1 account!",
        options=list(map(lambda name: discord.SelectOption(label=name, default=False), main.getCrewNames())),
        row=1
    )
    async def crew_select_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        self.crew = select.values[0]
        print(select.values[0])
        select = updateSelect(select)
        self.maybe_add_button()
        await interaction.response.edit_message(view=self)

    @discord.ui.string_select(
        placeholder="Choose the number of accounts the player has in the crew.",
        options=[discord.SelectOption(label=str(number), default=False) for number in range(1,11)],
        row=2
    )
    async def input_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        self.number=int(select.values[0])
        print(select.values[0])
        select = updateSelect(select)
        self.maybe_add_button()
        await interaction.response.edit_message(view=self)

class ScoreView(discord.ui.View):
    def __init__(self, ctx: discord.ApplicationContext):
        self.ctx=ctx
        self.crew=None
        self.score=None
        self.has_button=False
        super().__init__()
    
    @discord.ui.select(
        placeholder="Choose the crew for which you want to set the score!",
        options=list(map(lambda name: discord.SelectOption(label=name, default=False), main.getCrewNames())),
        row=0
    )
    async def select_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        select.disabled=True
        select = updateSelect(select)
        self.add_item(buttons.ScoreNextButton(self.ctx, select.values[0]))
        await interaction.response.edit_message(view=self)
    
    