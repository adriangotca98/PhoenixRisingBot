import discord
import utils
import constants
from score import buttons


class ScoreView(discord.ui.View):
    def __init__(self, ctx: discord.ApplicationContext):
        self.ctx = ctx
        self.crew = None
        self.score = None
        self.has_button = False
        super().__init__()
        options = set(utils.getCrewNames(constants.configCollection))
        options.difference_update(
            set(utils.getPushCrewNames(constants.configCollection))
        )
        options = list(sorted(options))
        utils.resetSelect(self, {"crew": options})

    @discord.ui.select(
        placeholder="Choose the crew for which you want to set the score!",
        row=0,
        custom_id="crew",
    )
    async def selectCallback(
        self, select: discord.ui.Select, interaction: discord.Interaction
    ):
        select.disabled = True
        select = utils.updateSelect(select)
        self.add_item(buttons.ScoreNextButton(self.ctx, str(select.values[0])))
        await interaction.response.edit_message(view=self)
