import discord
import main
import buttons


def update_select(select: discord.ui.Select):
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
        message = await main.getPlayersResponse(self.ctx, str(select.values[0]))
        await self.ctx.send_followup(message, ephemeral=True, delete_after=60)


class MultipleView(discord.ui.View):
    def __init__(self, ctx: discord.ApplicationContext):
        self.ctx = ctx
        self.player = None
        self.crew = None
        self.number = None
        self.has_button = False
        super().__init__()

    def maybe_add_button(self):
        if self.player is not None and self.crew is not None and self.number is not None and self.has_button is False:
            self.has_button = True
            self.add_item(buttons.MultipleButton(self.ctx, self.player, self.crew, self.number))

    @discord.ui.user_select(
        placeholder="Choose a player",
        row=0
    )
    async def user_select_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        if isinstance(select.values[0], discord.Member):
            self.player = select.values[0]
        self.maybe_add_button()
        await interaction.response.edit_message(view=self)

    @discord.ui.select(
        placeholder="Choose the crew where the player has more than 1 account!",
        options=list(map(lambda name: discord.SelectOption(label=name, default=False), main.getCrewNames())),
        row=1
    )
    async def crew_select_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        self.crew = str(select.values[0])
        select = update_select(select)
        self.maybe_add_button()
        await interaction.response.edit_message(view=self)

    @discord.ui.string_select(
        placeholder="Choose the number of accounts the player has in the crew.",
        options=[discord.SelectOption(label=str(number), default=False) for number in range(1, 11)],
        row=2
    )
    async def input_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        self.number = int(str(select.values[0]))
        select = update_select(select)
        self.maybe_add_button()
        await interaction.response.edit_message(view=self)


class ScoreView(discord.ui.View):
    def __init__(self, ctx: discord.ApplicationContext):
        self.ctx = ctx
        self.crew = None
        self.score = None
        self.has_button = False
        super().__init__()

    @discord.ui.select(
        placeholder="Choose the crew for which you want to set the score!",
        options=list(map(lambda name: discord.SelectOption(label=name, default=False), main.getCrewNames())),
        row=0
    )
    async def select_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        select.disabled = True
        select = update_select(select)
        self.add_item(buttons.ScoreNextButton(self.ctx, str(select.values[0])))
        await interaction.response.edit_message(view=self)


class KickBanUnbanView(discord.ui.View):
    def __init__(self, ctx: discord.ApplicationContext, bot: discord.Bot, op: str):
        super().__init__()
        self.ctx = ctx
        self.bot = bot
        self.op = op

    @discord.ui.user_select(
        placeholder="Select the user",
        row=0
    )
    async def callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        member = select.values[0]
        if isinstance(member, discord.Member):
            self.add_item(buttons.KickBanUnbanButton(self.ctx, self.bot, self.op, member))
        await interaction.response.edit_message(view=self)


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
        for idx1 in range(len(self.children)):
            select = self.children[idx1]
            if isinstance(select, discord.ui.Select):
                for idx2 in range(len(select.options)):
                    select.options[idx2].default = False
                self.children[idx1] = select

    def maybe_add_button(self):
        if (self.user is not None and self.crew_from is not None and self.crew_to is not None and
                self.season is not None):
            if self.next_buttons:
                for next_button in self.next_buttons:
                    self.remove_item(next_button)
            self.next_buttons = [
                buttons.TransferPingButton(self.ctx, self.user, self.crew_from, self.crew_to, self.season,
                                           self.should_kick),
                buttons.TransferNoPingButton(self.ctx, self.user, self.crew_from, self.crew_to, self.season,
                                             self.should_kick)]
            for next_button in self.next_buttons:
                self.add_item(next_button)

    @discord.ui.user_select(
        placeholder="Select the user",
        row=0
    )
    async def user_select_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        if isinstance(select.values[0], discord.Member):
            self.user = select.values[0]
        self.maybe_add_button()
        await interaction.response.edit_message(view=self)

    @discord.ui.string_select(
        placeholder="Where is the player going from?",
        row=1,
        options=list(
            map(lambda name: discord.SelectOption(label=name, default=False), ["New to family"] + main.getCrewNames()))
    )
    async def crew_from_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        self.crew_from = str(select.values[0])
        select = update_select(select)
        self.maybe_add_button()
        await interaction.response.edit_message(view=self)

    @discord.ui.string_select(
        placeholder="Where is the player going to?",
        row=2,
        options=list(map(lambda name: discord.SelectOption(label=name, default=False),
                         ["Out of family - kick", "Out of family - keep community"] + main.getCrewNames()))
    )
    async def crew_to_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        self.crew_to = str(select.values[0])
        if self.crew_to.endswith("kick"):
            self.should_kick = True
        if self.crew_to.startswith("Out of family"):
            self.crew_to = "Out of family"
        select = update_select(select)
        self.maybe_add_button()
        await interaction.response.edit_message(view=self)

    @discord.ui.string_select(
        placeholder="Season",
        row=3,
        options=list(map(lambda name: discord.SelectOption(label=name, default=False),
                         [f"current ({main.getCurrentSeason()})", str(main.getCurrentSeason() + 1),
                          str(main.getCurrentSeason() + 2), str(main.getCurrentSeason() + 3),
                          str(main.getCurrentSeason() + 4)]))
    )
    async def season_select(self, select: discord.ui.Select, interaction: discord.Interaction):
        season = main.getCurrentSeason() + 4
        while str(season) != select.values[0] and season > main.getCurrentSeason():
            season -= 1
        self.season = season
        select = update_select(select)
        self.maybe_add_button()
        await interaction.response.edit_message(view=self)


class CancelTransferView(discord.ui.View):
    def __init__(self, ctx: discord.ApplicationContext):
        super().__init__()
        self.ctx = ctx
        self.user = None
        self.crew_from = None
        self.crew_to = None
        self.next_buttons = None

    def maybe_add_button(self):
        if self.user is not None and self.crew_from is not None and self.crew_to is not None:
            if self.next_buttons:
                for next_button in self.next_buttons:
                    self.remove_item(next_button)
            self.next_buttons = [buttons.CancelTransferPingButton(self.ctx, self.user, self.crew_from, self.crew_to),
                                 buttons.CancelTransferNoPingButton(self.ctx, self.user, self.crew_from, self.crew_to)]
            for next_button in self.next_buttons:
                self.add_item(next_button)

    @discord.ui.user_select(
        placeholder="Select the user",
        row=0
    )
    async def user_select_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        if isinstance(select.values[0], discord.Member):
            self.user = select.values[0]
        self.maybe_add_button()
        await interaction.response.edit_message(view=self)

    @discord.ui.string_select(
        placeholder="Where is the player going from?",
        min_values=0,
        row=1,
        options=list(
            map(lambda name: discord.SelectOption(label=name, default=False), ["New to family"] + main.getCrewNames()))
    )
    async def crew_from_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        self.crew_from = str(select.values[0])
        select = update_select(select)
        self.maybe_add_button()
        await interaction.response.edit_message(view=self)

    @discord.ui.string_select(
        placeholder="Where is the player going to?",
        min_values=0,
        row=2,
        options=list(
            map(lambda name: discord.SelectOption(label=name, default=False), ["Out of family"] + main.getCrewNames()))
    )
    async def crew_to_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        self.crew_to = str(select.values[0])
        select = update_select(select)
        self.maybe_add_button()
        await interaction.response.edit_message(view=self)
