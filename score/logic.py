import discord
import utils
import constants


async def setScore(ctx: discord.ApplicationContext, crewName: str, score: str):
    print(f"Setting score {str(score)} for {crewName}")
    channelId = (
        utils.getDbField(constants.crewCollection, crewName, "leaderboard_id") or -1
    )
    if not isinstance(channelId, int):
        return
    channel = ctx.bot.get_channel(channelId)
    if not isinstance(channel, discord.TextChannel):
        return
    channelName = channel.name
    newChannelName = channelName.strip("0123456789'`’") + utils.getScoreWithSeparator(
        int(score)
    )
    await channel.edit(name=newChannelName)
    constants.scores[crewName] = int(score)
    await reorderChannels(ctx, constants.scores, crewName)


async def reorderChannels(
    ctx: discord.ApplicationContext, scoresDict: dict, crewName: str
):
    sortedScores = dict(
        sorted(scoresDict.items(), key=lambda item: item[1], reverse=True)
    )
    channelId = (
        utils.getDbField(constants.crewCollection, crewName, "leaderboard_id") or -1
    )
    if not isinstance(channelId, int):
        return
    channel = ctx.bot.get_channel(channelId)
    if list(sortedScores.keys())[0] == crewName:
        if isinstance(channel, discord.TextChannel):
            await channel.move(beginning=True)
        return
    lastKey = ""
    for key in sortedScores:
        if key == crewName:
            aboveChannelId = utils.getDbField(
                constants.crewCollection, lastKey, "leaderboard_id"
            )
            if aboveChannelId is None or not isinstance(aboveChannelId, int):
                continue
            aboveChannel = ctx.bot.get_channel(aboveChannelId)
            if isinstance(channel, discord.TextChannel) and aboveChannel is not None:
                await channel.move(after=aboveChannel)
            return
        lastKey = key
