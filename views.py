from numpy import isin
import utils
import discord
import constants
import main
import buttons
import modals


def updateSelect(select: discord.ui.Select):
    for idx in range(len(select.options)):
        select.options[idx].default = False
        if select.options[idx].label == select.values[0]:
            select.options[idx].default = True
    return select


class EndPushView(discord.ui.View):
    def __init__(self, ctx: discord.ApplicationContext):
        super().__init__()
        self.ctx = ctx
        self.crew_name = None
        for child in self.children:
            if isinstance(child, discord.ui.Select):
                child.options = list(
                    map(
                        lambda name: discord.SelectOption(label=name, default=False),
                        utils.getPushCrewNames(constants.configCollection),
                    )
                )

    @discord.ui.string_select(placeholder="Push crew")
    async def callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        if isinstance(select.values[0], str):
            message = main.endPush(select.values[0])
            await interaction.response.send_message(message, ephemeral=True, delete_after=60)


class StartPushView(discord.ui.View):
    def __init__(self, ctx: discord.ApplicationContext):
        super().__init__()
        self.ctx = ctx
        self.role = None
        self.members_channel = None
        self.chat_channel = None

    async def maybeSendModal(self, interaction: discord.Interaction):
        if self.role is not None and self.members_channel is not None and self.chat_channel is not None:
            await interaction.response.send_modal(modals.StartPushModal(self.ctx, self.role, self.members_channel, self.chat_channel))
        else:
            await interaction.response.edit_message(view=self)

    @discord.ui.role_select(
        placeholder="Choose the role for the Top 10 push crew",
    )
    async def roleSelectCallback(self, select: discord.ui.Select, interaction: discord.Interaction):
        if isinstance(select.values[0], discord.Role):
            self.role = select.values[0]
        await self.maybeSendModal(interaction)
    
    @discord.ui.channel_select(
        placeholder='Choose the members channel for the members list',
    )
    async def membersChannelSelectCallback(self, select: discord.ui.Select, interaction: discord.Interaction):
        if isinstance(select.values[0], discord.TextChannel):
            self.members_channel = select.values[0]
        await self.maybeSendModal(interaction)
    
    @discord.ui.channel_select(
        placeholder='Choose the members channel for the members list',
    )
    async def chatChannelSelectCallback(self, select: discord.ui.Select, interaction: discord.Interaction):
        if isinstance(select.values[0], discord.TextChannel):
            self.chat_channel = select.values[0]
        await self.maybeSendModal(interaction)


class FawkesView(discord.ui.View):
    def __init__(self, ctx: discord.ApplicationContext, bot: discord.Bot):
        self.ctx = ctx
        self.bot = bot
        super().__init__()

    @discord.ui.select(
        placeholder="Pick an operation to be performed by Fawkes",
        options=list(
            map(lambda name: discord.SelectOption(label=name), constants.commandsList)
        ),
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


class MakeTransfersView(discord.ui.View):
    def __init__(self, ctx: discord.ApplicationContext):
        self.ctx = ctx
        super().__init__()

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def yesButtonCallback(
        self, button: discord.Button, interaction: discord.Interaction
    ):
        self.disable_all_items()
        message = await main.makeTransfers(self.ctx)
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


class MembersCrewsView(discord.ui.View):
    def __init__(self, ctx: discord.ApplicationContext):
        self.ctx = ctx
        super().__init__()
        for child in self.children:
            if isinstance(child, discord.ui.Select):
                child.options = list(
                    map(
                        lambda name: discord.SelectOption(label=name, default=False),
                        utils.getCrewNames(constants.configCollection),
                    )
                )

    @discord.ui.select(placeholder="Pick a crew to update members for!")
    async def selectCallback(
        self, select: discord.ui.Select, interaction: discord.Interaction
    ):
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
        optionsMap = {
            "crew": list(
                map(
                    lambda name: discord.SelectOption(label=name, default=False),
                    utils.getCrewNames(constants.configCollection),
                )
            ),
            "number_of_accounts": [
                discord.SelectOption(label=str(number), default=False)
                for number in range(1, 11)
            ],
        }
        for child in self.children:
            if isinstance(child, discord.ui.Select) and child.custom_id in optionsMap:
                child.options = optionsMap[child.custom_id]

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
        select = updateSelect(select)
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
        select = updateSelect(select)
        self.maybeAddButton()
        await interaction.response.edit_message(view=self)


class ScoreView(discord.ui.View):
    def __init__(self, ctx: discord.ApplicationContext):
        self.ctx = ctx
        self.crew = None
        self.score = None
        self.has_button = False
        super().__init__()
        options = set(utils.getCrewNames(constants.configCollection))
        options.difference_update(set(utils.getPushCrewNames(constants.configCollection)))
        for child in self.children:
            if isinstance(child, discord.ui.Select):
                child.options = list(
                    map(
                        lambda name: discord.SelectOption(label=name, default=False),
                        options
                    )
                )

    @discord.ui.select(
        placeholder="Choose the crew for which you want to set the score!", row=0
    )
    async def selectCallback(
        self, select: discord.ui.Select, interaction: discord.Interaction
    ):
        select.disabled = True
        select = updateSelect(select)
        self.add_item(buttons.ScoreNextButton(self.ctx, str(select.values[0])))
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
        optionsMap = {
            "crew_from": list(
                map(
                    lambda name: discord.SelectOption(label=name, default=False),
                    ["New to family"] + utils.getCrewNames(constants.configCollection),
                )
            ),
            "crew_to": list(
                map(
                    lambda name: discord.SelectOption(label=name, default=False),
                    ["Out of family - kick", "Out of family - keep community"]
                    + utils.getCrewNames(constants.configCollection),
                )
            ),
            "season": list(
                map(
                    lambda name: discord.SelectOption(label=name, default=False),
                    [
                        str(utils.getCurrentSeason(constants.configCollection)),
                        str(utils.getCurrentSeason(constants.configCollection) + 1),
                        str(utils.getCurrentSeason(constants.configCollection) + 2),
                        str(utils.getCurrentSeason(constants.configCollection) + 3),
                        str(utils.getCurrentSeason(constants.configCollection) + 4),
                    ],
                )
            ),
        }
        for child in self.children:
            if isinstance(child, discord.ui.Select) and child.custom_id in optionsMap:
                child.options = optionsMap[child.custom_id]

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
        select = updateSelect(select)
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
        select = updateSelect(select)
        self.maybeAddButton()
        await interaction.response.edit_message(view=self)

    @discord.ui.string_select(placeholder="Season", row=3, custom_id="season")
    async def seasonSelectCallback(
        self, select: discord.ui.Select, interaction: discord.Interaction
    ):
        self.season = int(str(select.values[0]))
        select = updateSelect(select)
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
        optionsMap = {
            "crew_from": list(
                map(
                    lambda name: discord.SelectOption(label=name, default=False),
                    ["New to family"] + utils.getCrewNames(constants.configCollection),
                )
            ),
            "crew_to": list(
                map(
                    lambda name: discord.SelectOption(label=name, default=False),
                    ["Out of family - kick", "Out of family - keep community"]
                    + utils.getCrewNames(constants.configCollection),
                )
            ),
        }
        for child in self.children:
            if isinstance(child, discord.ui.Select) and child.custom_id in optionsMap:
                child.options = optionsMap[child.custom_id]

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
        select = updateSelect(select)
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
        select = updateSelect(select)
        self.maybeAddButton()
        await interaction.response.edit_message(view=self)


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
        select = updateSelect(select)
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
        select = updateSelect(select)
        self.maybeAddButton()
        await interaction.response.edit_message(view=self)
