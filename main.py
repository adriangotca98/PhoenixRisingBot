import discord
import pymongo
import utils
import constants


class Member:
    def __init__(
        self, admin: bool, leader: bool, member_id: int, name: str, multiple: int
    ):
        self.admin = admin
        self.leader = leader
        self.member_id = member_id
        self.name = name
        self.multiple = multiple


def sortFunction(member: Member):
    if member.leader:
        return "0 " + member.name
    if member.admin:
        return "1 " + member.name
    return "2 " + member.name


async def init(bot: discord.Bot):
    crewNames = utils.getCrewNames(constants.configCollection)
    if crewNames is None:
        return
    for crew in crewNames:
        channelId = (
            utils.getDbField(constants.crewCollection, crew, "leaderboard_id")
        )
        if not isinstance(channelId, int):
            continue
        channel = bot.get_channel(channelId)
        if not isinstance(channel, discord.TextChannel):
            continue
        constants.scores[crew] = utils.computeScoreFromChannelName(channel.name)


def startPush(role: discord.Role, membersChannel: discord.TextChannel, chatChannel: discord.TextChannel, crewName: str):
    constants.configCollection.update_one({"key": "crews"}, {"$push": {"value": crewName}})
    constants.configCollection.update_one({"key": "crew_region"},  {"$push": {f"value.PUSH": crewName}})
    constants.vacanciesCollection.update_one({}, {"$set": {crewName: {"current": 0, "next": 0}}})
    constants.crewCollection.insert_one({
        "member": role.id,
        "key": crewName,
        "members_channel_id": membersChannel.id,
        "chat_channel_id": chatChannel.id
    })
    return "Push registered successfully."


def endPush(crewName):
    constants.configCollection.update_one({"key": "crews"}, {"$pull": {"value": crewName}})
    constants.configCollection.update_one({"key": "crew_region"},  {"$pull": {f"value.PUSH": crewName}})
    constants.vacanciesCollection.update_one({}, {"$unset": {crewName: ""}})
    constants.crewCollection.delete_one({"key": crewName})
    return "Push crew removed from tracking successfully."


async def addOrRemoveRoleAndUpdateMultiple(
    ctx: discord.ApplicationContext,
    player: discord.Member,
    transfer: dict,
    crewName: str,
    op: str,
):
    numberOfAccounts = transfer["number_of_accounts"]
    crewRoleId = utils.getDbField(constants.crewCollection, crewName, "member")
    if not isinstance(crewRoleId, int):
        return
    crewRole = utils.getRole(ctx, crewRoleId)
    if crewRole is None:
        return
    multipleEntry = (
        constants.multipleAccountsCollection.find_one({"key": crewName}) or {}
    )
    if op == "ADD":
        currentMultiple = 0
        if player.get_role(crewRole.id):
            currentMultiple = multipleEntry.get(str(player.id)) or 1
        newMultiple = currentMultiple + numberOfAccounts
        if newMultiple > 1:
            constants.multipleAccountsCollection.update_one(
                {"key": crewName}, {"$set": {str(player.id): newMultiple}}, upsert=True
            )
        await player.add_roles(crewRole)
    else:
        currentMultiple = multipleEntry.get(str(player.id)) or 1
        if currentMultiple - numberOfAccounts <= 1:
            constants.multipleAccountsCollection.update_one(
                {"key": crewName}, {"$unset": {str(player.id): ""}}
            )
            if currentMultiple - numberOfAccounts == 0:
                await player.remove_roles(crewRole)
        else:
            constants.multipleAccountsCollection.update_one(
                {"key": crewName},
                {"$set": {str(player.id): currentMultiple - numberOfAccounts}},
            )


async def makeTransfers(ctx: discord.ApplicationContext):
    currentSeason = utils.getCurrentSeason(constants.configCollection)
    if ctx.guild is None:
        return "Something is terribly wrong. Contact server admins."
    transfers = list(constants.movesCollection.find({"season": currentSeason}))
    crewsToUpdateMembers = set()
    for transfer in transfers:
        print(f"Processing {transfer}")
        try:
            player = await ctx.guild.fetch_member(transfer["player"])
        except (discord.Forbidden, discord.HTTPException):
            constants.movesCollection.delete_many({"player": transfer["player"]})
            continue
        await addOrRemoveRoleAndUpdateMultiple(
            ctx, player, transfer, transfer["crew_from"], "REMOVE"
        )
        await addOrRemoveRoleAndUpdateMultiple(
            ctx, player, transfer, transfer["crew_to"], "ADD"
        )
        if transfer["crew_to"] == "Out of family":
            shouldKick = transfer.get("should_kick") or False
            if shouldKick:
                await player.kick(reason="Kicked by Fawkes via transfer")
            else:
                communityMemberRole = utils.getRole(
                    ctx, constants.communityMemberRoleId
                )
                if communityMemberRole is not None:
                    await player.add_roles(communityMemberRole)
        constants.movesCollection.delete_one(transfer)
        await deleteMovementFromMessage(ctx, transfer["crew_from"], "OUT")
        await deleteMovementFromMessage(ctx, transfer["crew_to"], "IN")
        crewsToUpdateMembers.add(transfer["crew_from"])
        crewsToUpdateMembers.add(transfer["crew_to"])
    for crew in crewsToUpdateMembers:
        if crew not in ["New to family", "Out of family"]:
            await getPlayersResponse(ctx, crew)
    return "All good"


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


async def updateMessage(
    ctx: discord.ApplicationContext, crewData, keyToSet, initialMessage
):
    key = crewData["key"]
    channelId = crewData["members_channel_id"]
    channel = ctx.bot.get_channel(channelId)
    if isinstance(channel, discord.TextChannel):
        message = await channel.send(initialMessage)
        constants.crewCollection.update_one(
            {"key": key}, {"$set": {keyToSet: message.id}}
        )
        return message
    return None


async def getMessage(
    ctx, crewData: dict, keyToGet: str, channelKey: str, initialMessage: str
):
    if keyToGet not in crewData.keys():
        message = await updateMessage(ctx, crewData, keyToGet, initialMessage)
    else:
        channelId = crewData[channelKey]
        channel = ctx.bot.get_channel(channelId)
        try:
            message = await channel.fetch_message(crewData[keyToGet])
        except discord.errors.NotFound:
            print("Message not found. Creating another one :)")
            message = await updateMessage(ctx, crewData, keyToGet, initialMessage)
    return message


def getMembers(
    guild: discord.Guild,
    crewName: str,
    adminRole: discord.Role | None,
    leaderRole: discord.Role | None,
    memberRole: discord.Role,
    multipleAccountsIds,
    multipleAccountsData,
):
    response = []

    for member in guild.members:
        memberStruct = Member(False, False, member.id, member.display_name, 0)
        memberId = str(member.id)
        if adminRole is not None and member.get_role(adminRole.id):
            memberStruct.admin = True
        if leaderRole is not None and member.get_role(leaderRole.id):
            memberStruct.leader = True
        if member.get_role(memberRole.id):
            response.append(memberStruct)
        if memberId in multipleAccountsIds:
            if member.get_role(memberRole.id):
                for i in range(multipleAccountsData[memberId] - 1):
                    newMemberStruct = Member(
                        False, False, member.id, member.display_name, i + 2
                    )
                    response.append(newMemberStruct)
            else:
                constants.multipleAccountsCollection.update_one(
                    {"key": crewName}, {"$unset": {memberId: ""}}
                )
    return response


async def getPlayersResponse(ctx: discord.ApplicationContext, key: str):
    multipleAccountsData = constants.multipleAccountsCollection.find_one(
        {"key": key}, {"_id": 0}
    )
    if multipleAccountsData is not None:
        multipleAccountsIds = [key for key in multipleAccountsData if key != "key"]
    else:
        multipleAccountsIds = []
    crewData = constants.crewCollection.find_one({"key": key}, {"_id": 0}) or {}
    memberRoleId = utils.getDbField(constants.crewCollection, key, "member") or -1
    adminRoleId = utils.getDbField(constants.crewCollection, key, "admin") or -1
    leaderRoleId = utils.getDbField(constants.crewCollection, key, "leader") or -1
    if (
        not isinstance(memberRoleId, int)
        or not isinstance(adminRoleId, int)
        or not isinstance(leaderRoleId, int)
    ):
        return
    memberRole = utils.getRole(ctx, memberRoleId)
    adminRole = utils.getRole(ctx, adminRoleId)
    leaderRole = utils.getRole(ctx, leaderRoleId)
    if memberRole is None:
        return
    crewName = memberRole.name
    message = await getMessage(
        ctx,
        crewData,
        "message_id",
        "members_channel_id",
        "**__Members for " + crewName.upper() + "__**",
    )
    guild = ctx.guild
    if guild is None:
        return
    response = getMembers(
        guild,
        crewName,
        adminRole,
        leaderRole,
        memberRole,
        multipleAccountsIds,
        multipleAccountsData,
    )
    response.sort(key=sortFunction)
    await updateVacancies(ctx, key, response)

    stringResponse = "**__Members of " + crewName.upper() + "__**\n"
    number = 1
    for member in response:
        stringResponse += str(number) + ". <@!" + str(member.member_id) + ">"
        if member.multiple:
            stringResponse += " " + str(member.multiple)
        if member.leader:
            stringResponse += " -> **Leader**"
        elif member.admin:
            stringResponse += " -> *Admin*"
        stringResponse += "\n"
        number += 1
    if message is not None:
        await message.edit(content=stringResponse)
    return "OK, all good."


async def updateVacancies(
    ctx: discord.ApplicationContext, crew_name: str, members_list: list = []
):
    currentSeason = utils.getCurrentSeason(constants.configCollection)
    currentSeasonCount = len(members_list)
    vacanciesEntry = constants.vacanciesCollection.find_one({}) or {}
    if crew_name == "New to family" or crew_name == "Out of family":
        return
    if currentSeasonCount == 0:
        if crew_name in vacanciesEntry:
            currentSeasonCount = vacanciesEntry[crew_name]["current"]
        else:
            currentSeasonCount = 0
    nextSeasonCount = currentSeasonCount
    for move in list(
        constants.movesCollection.find(
            {"crew_to": crew_name, "season": currentSeason + 1}
        )
    ):
        nextSeasonCount += move["number_of_accounts"]
    for move in list(
        constants.movesCollection.find(
            {"crew_from": crew_name, "season": currentSeason + 1}
        )
    ):
        nextSeasonCount -= move["number_of_accounts"]
    constants.vacanciesCollection.update_one(
        {},
        {"$set": {crew_name: {"current": currentSeasonCount, "next": nextSeasonCount}}},
    )
    if crew_name in utils.getCrewNames(constants.configCollection):
        vacanciesEntry[crew_name]["current"] = currentSeasonCount
        vacanciesEntry[crew_name]["next"] = nextSeasonCount
    messageContent = "**__Latest Crew Vacancies__**\n\n"
    crewRegion = utils.getCrewRegion(constants.configCollection)
    for region in crewRegion.keys():
        messageContent += f"**__{region} Crews__**\n\n"
        for crew_name in crewRegion[region]:
            if crew_name not in vacanciesEntry.keys():
                continue
            messageContent += (
                f"**{crew_name.capitalize()}**\n{vacanciesEntry[crew_name]['current']}/30 Current Season"
                f"\n{vacanciesEntry[crew_name]['next']}/30 Next Season\n"
            )
        messageContent += "\n"
    guild = ctx.guild
    if guild is not None:
        channel = guild.get_channel(constants.vacanciesChannelId)
        try:
            if isinstance(channel, discord.TextChannel):
                message = await channel.fetch_message(constants.vacanciesMessageId)
                await message.edit(content=messageContent)
        except discord.errors.NotFound:
            if isinstance(channel, discord.TextChannel):
                message = await channel.send(messageContent)
                constants.configCollection.update_one(
                    {"key": "IDs"}, {"$set": {"vacancies_message_id": message.id}}
                )


async def deleteMovementFromMessage(
    ctx: discord.ApplicationContext, crewName: str, inOrOut: str
):
    crewData = constants.crewCollection.find_one({"key": crewName})
    if crewData is None:
        return
    if inOrOut == "IN":
        messageIdKey = "in_message_id"
        initialMessage = "Players Joining:"
    else:
        messageIdKey = "out_message_id"
        initialMessage = "Players Leaving:"
    message = await getMessage(
        ctx, crewData, messageIdKey, "members_channel_id", initialMessage
    )
    await updateMovementsMessage(ctx, message, crewName, inOrOut)


async def kickOrBanOrUnban(
    user: discord.Member, op: str, bot: discord.Bot, reason: str | None = None
):
    for guild in bot.guilds:
        if guild.id == constants.risingServerId:
            print(
                "Doing "
                + op
                + " for user: "
                + user.name
                + " in the server named: "
                + guild.name
            )
            if op == "kick":
                await guild.kick(user, reason=reason)
            elif op == "ban":
                await guild.ban(user, reason=reason)
            elif op == "unban":
                await guild.unban(user, reason=reason)


def processMultiple(user: discord.Member, crewName: str, numberOfAccounts: int):
    memberRoleId = utils.getDbField(constants.crewCollection, crewName, "member")
    if not isinstance(memberRoleId, int):
        return "Database error. Contact @AdrianG98RO for fixing it."
    if not user.get_role(memberRoleId):
        return "User does not have crew role! Add crew role and try again."
    memberId = str(user.id)
    if numberOfAccounts != 1:
        constants.multipleAccountsCollection.find_one_and_update(
            {"key": crewName}, {"$set": {memberId: numberOfAccounts}}, upsert=True
        )
    else:
        constants.multipleAccountsCollection.find_one_and_update(
            {"key": crewName}, {"$unset": {memberId: ""}}
        )
    return "Multiple accounts recorded!"


async def processTransfer(
    ctx: discord.ApplicationContext,
    player: discord.Member,
    crewFrom: str,
    crewTo: str,
    numberOfAccounts: int,
    season: int,
    pingAdmin: bool,
    shouldKick: bool,
):
    if crewFrom == "New to family" and crewTo == "Out of family":
        return (
            "A player can't be new to family and going out of family at the same time"
        )
    if crewFrom == crewTo:
        return "A move can't take place within the same crew."
    if crewTo == "Out of family" and shouldKick is None:
        return "Set should_kick for this kind of move."
    if season < utils.getCurrentSeason(constants.configCollection):
        return "Transfers can only happen in the future or in the current season"
    message = await processMovement(
        ctx, crewFrom, crewTo, player, numberOfAccounts, season, pingAdmin, shouldKick
    )
    return message


def checkRole(ctx: discord.ApplicationContext, player: discord.Member, crewName: str):
    crewData = constants.crewCollection.find_one(
        {"key": crewName}, {"_id": 0, "member": 1}
    )
    if crewName == "New to family":
        return True
    if crewData is None:
        return False
    roleId = crewData.get("member")
    if player.get_role(roleId) is None:
        return False
    return True


def checkHistory(
    ctx: discord.ApplicationContext, player: discord.Member, crewName: str, season: int
):
    movesData = list(
        constants.movesCollection.find({"player": player.id, "season": {"$lt": season}})
    )
    movesData.sort(key=lambda elem: elem.get("season"))
    if len(movesData) != 0:
        lastMove = movesData[-1]
        if lastMove.get("crew_to") != crewName:
            return (
                False,
                f"I looked at this player history of movements and from what I can see, he will NOT be in "
                f"**{crewName}** at the time of the transfer. "
                f"Last move is registered to {lastMove.get('crew_to')} in season {lastMove('season')}. "
                f"If your move is before that you'll have to redo the path till then so we don't risk missing links"
                f" between seasons. Talk with <@308561593858392065> about how to do this.",
            )
        return True, "history"
    hasRole = checkRole(ctx, player, crewName)
    if not hasRole:
        return (
            False,
            "The player does not have the crew role. Add the role and try again.",
        )
    return True, "crew_role"


def checkForNumberOfAccounts(
    player: discord.Member, crewName: str, season: int, numberOfAccountsToMoveNext: int
):
    multipleData = constants.multipleAccountsCollection.find_one(
        {"key": crewName}, {"_id": 0, str(player.id): 1}
    )
    if multipleData is None or str(player.id) not in multipleData.keys():
        numberOfAccountsAvailableToMove = 1
    else:
        numberOfAccountsAvailableToMove = multipleData[str(player.id)]
    movesBeforeTheSeason = constants.movesCollection.find(
        {"player": player.id, "crew_from": crewName, "season": {"$lt": season}}
    )
    for move in movesBeforeTheSeason:
        numberOfAccountsAvailableToMove -= move.get("number_of_accounts") or 1
    existingMovesData = constants.movesCollection.find(
        {"player": player.id, "crew_from": crewName}
    )
    for existingMove in existingMovesData:
        numAccounts = existingMove.get("number_of_accounts") or 1
        numberOfAccountsAvailableToMove -= numAccounts
    return numberOfAccountsAvailableToMove >= numberOfAccountsToMoveNext


async def processMovement(
    ctx: discord.ApplicationContext,
    crewFrom: str,
    crewTo: str,
    player: discord.Member,
    numberOfAccounts: int,
    season: int,
    pingAdmin: bool,
    shouldKick: bool,
) -> str:
    historyCheck = checkHistory(ctx, player, crewFrom, season)
    if not historyCheck[0]:
        return historyCheck[1]
    if not checkForNumberOfAccounts(player, crewFrom, season, numberOfAccounts):
        return (
            "The player has too many accounts registered to transfer with this transfer included. "
            "Check the multiple or remove from the existing transfers for this player first."
        )
    movementData = constants.movesCollection.find_one(
        {"player": player.id, "crew_from": crewFrom, "crew_to": crewTo}
    )
    if movementData is not None:
        constants.movesCollection.delete_one(
            {"player": player.id, "crew_from": crewFrom, "crew_to": crewTo}
        )
    objectToInsert = {
        "player": player.id,
        "crew_from": crewFrom,
        "crew_to": crewTo,
        "number_of_accounts": numberOfAccounts,
        "season": season,
        "should_kick": shouldKick
    }
    constants.movesCollection.insert_one(objectToInsert)
    crewFromData = constants.crewCollection.find_one({"key": crewFrom}, {"_id": 0})
    if crewFromData is not None:
        outMessage = await getMessage(
            ctx, crewFromData, "out_message_id", "members_channel_id", "**OUT:**"
        )
        await updateMovementsMessage(ctx, outMessage, crewFrom, "OUT")
    crewToData = constants.crewCollection.find_one({"key": crewTo}, {"_id": 0})
    if crewToData is not None:
        inMessage = await getMessage(
            ctx, crewToData, "in_message_id", "members_channel_id", "**IN:**"
        )
        await updateMovementsMessage(ctx, inMessage, crewTo, "IN")
    await updateVacancies(ctx, crewFrom)
    await updateVacancies(ctx, crewTo)
    await sendMessageToAdminChat(
        ctx, crewTo, player, "confirm", "to", pingAdmin, season, numberOfAccounts
    )
    await sendMessageToAdminChat(
        ctx, crewFrom, player, "confirm", "from", pingAdmin, season, numberOfAccounts
    )
    if season == utils.getCurrentSeason(constants.configCollection):
        await makeTransfers(ctx)
    return "Transfer processed successfully"


async def sendMessageInChat(ctx: discord.ApplicationContext, crew: str, player: discord.Member, confirmOrCancel: str, toOrFrom: str, numberOfAccounts: int):
    if confirmOrCancel != "confirm" or toOrFrom == 'to':
        return
    crewData = constants.crewCollection.find_one({"key": crew})
    if crewData is None:
        return
    message = (
        f"Thanks for your interest in running in {crew}!"
        f"You've been selected to run in {crew} with {numberOfAccounts} accounts, {player.mention}. Good luck!"
    )
    channel = ctx.bot.get_channel(crewData.get("chat_channel_id") or -1)
    if isinstance(channel, discord.TextChannel):
        await channel.send(message)


async def sendMessageToAdminChat(
    ctx: discord.ApplicationContext,
    crew: str,
    player: discord.Member,
    confirmOrCancel: str,
    toOrFrom: str,
    pingAdmin: bool,
    season: int,
    numberOfAccounts: int,
):
    if not pingAdmin:
        return
    crewData = constants.crewCollection.find_one(
        {"key": crew}, {"admin_channel_id": 1, "admin": 1, "_id": 0}
    )
    if crewData is None:
        return
    if crewData.get("admin") == None:
        await sendMessageInChat(ctx, crew, player, confirmOrCancel, toOrFrom, numberOfAccounts)
        return
    adminRole = utils.getRole(ctx, crewData.get("admin"))
    if adminRole is None:
        return
    message = ""
    if confirmOrCancel == "confirm" and ctx.author:
        message = (
            f"{adminRole.mention},\n{ctx.author.mention} confirmed that {player.mention} will be moving "
            f"{toOrFrom} your crew in S{season} with {numberOfAccounts} account"
        ) + ("s." if numberOfAccounts > 1 else ".")
    elif ctx.author:
        message = (
            f"{adminRole.mention},\n{ctx.author.mention} has just canceled a scheduled move of {player.mention} "
            f"{toOrFrom} your crew in S{season} with {numberOfAccounts} account"
        ) + ("s." if numberOfAccounts > 1 else ".")
    channel = ctx.bot.get_channel(crewData.get("admin_channel_id") or -1)
    if isinstance(channel, discord.TextChannel):
        await channel.send(message)


async def updateMovementsMessage(
    ctx: discord.ApplicationContext, message, crewName, inOrOut
):
    newMessage = f"**Players {'Joining' if inOrOut == 'IN' else 'Leaving'}:**\n\n"
    movementsKey = "crew_from" if inOrOut == "OUT" else "crew_to"
    crewKey = "crew_to" if inOrOut == "OUT" else "crew_from"
    movements = constants.movesCollection.find({movementsKey: crewName}, {"_id": 0})
    idx = 1
    for move in movements:
        crewData = constants.crewCollection.find_one({"key": move[crewKey]}, {"_id": 0})
        try:
            guild = ctx.guild
            if guild is not None:
                member = await guild.fetch_member(move.get("player"))
            else:
                member = None
        except (discord.Forbidden, discord.HTTPException):
            constants.movesCollection.delete_many({"player": move.get("player")})
            continue
        if member is not None:
            newMessage += f"{str(idx)}. {member.mention} "
        if crewData is None:
            newMessage += f"{move[crewKey]} in S{str(move['season'])}"
        else:
            crewRole = utils.getRole(ctx, crewData["member"])
            numberOfAccounts = move["number_of_accounts"]
            newMessage += (
                f'{"from" if inOrOut == "IN" else "to"} {crewRole.mention if crewRole is not None else ""}'
                f'{f" with {numberOfAccounts} accounts" if numberOfAccounts > 1 else ""} in '
                f'S{str(move["season"])}'
            )
        newMessage += "\n"
        idx += 1
    await message.edit(newMessage)


async def unregisterTransfer(
    ctx: discord.ApplicationContext,
    player: discord.Member,
    crewFrom,
    crewTo,
    pingAdmin=True,
):
    if crewTo != crewFrom and (crewTo is None or crewFrom is None):
        return (
            "if you give one of crew_from and crew_to, you must give the other as well."
        )
    if crewTo == crewFrom and crewTo is not None:
        return "A movement can't be within the same crew, so I also can't unregister this kind of moves."
    if crewTo is None:
        moves = list(constants.movesCollection.find({"player": player.id}))
        if len(moves) == 0:
            return "No moves found for this player."
        if len(moves) > 1:
            return "Too many moves found, add crew_from and crew_to and try again."
        move = moves[0]
    else:
        move = list(
            constants.movesCollection.find(
                {"player": player.id, "crew_from": crewFrom, "crew_to": crewTo}
            )
        )[0]
    constants.movesCollection.delete_one({"player": move["player"]})
    await deleteMovementFromMessage(ctx, move["crew_from"], "OUT")
    await deleteMovementFromMessage(ctx, move["crew_to"], "IN")
    await updateVacancies(ctx, move["crew_from"])
    await updateVacancies(ctx, move["crew_to"])
    await sendMessageToAdminChat(
        ctx,
        move["crew_to"],
        player,
        "cancel",
        "to",
        pingAdmin,
        move["season"],
        move["number_of_accounts"],
    )
    await sendMessageToAdminChat(
        ctx,
        move["crew_from"],
        player,
        "cancel",
        "from",
        pingAdmin,
        move["season"],
        move["number_of_accounts"],
    )
    return f"Cancelled transfer for {player.name} from {crewFrom} to {crewTo}"


def getOverwritesFromDust(
    ctx: discord.ApplicationContext,
    guild: discord.Guild,
    memberRole: discord.Role,
    channelOrCategory: str = "CATEGORY",
):
    dustData = constants.crewCollection.find_one({"key": "dust"}) or {}
    dustCategoryId = dustData.get("category_id", -1)
    dustCategory = guild.get_channel(dustCategoryId)
    dustMemberRole = utils.getRole(ctx, dustData.get("member", -1))
    if not isinstance(dustCategory, discord.CategoryChannel) or dustMemberRole is None:
        return {}
    dustChatChannel = list(
        filter(lambda channel: channel.name.endswith("chat"), dustCategory.channels)
    )[0]
    categoryOverwrites = dustCategory.overwrites
    categoryOverwrites[memberRole] = categoryOverwrites[dustMemberRole]
    del categoryOverwrites[dustMemberRole]
    channelOverwrites = dustChatChannel.overwrites
    channelOverwrites[memberRole] = channelOverwrites[dustMemberRole]
    del channelOverwrites[dustMemberRole]
    if channelOrCategory == "CHANNEL":
        return channelOverwrites
    return categoryOverwrites


def getBelowCrewData(shortname: str):
    return (
        constants.crewCollection.find_one(
            {
                "$and": [
                    {"key": {"$gt": shortname}},
                    {"key": {"$ne": "fire"}},
                    {"key": {"$ne": "ice"}},
                ]
            },
            sort={"key": pymongo.ASCENDING},
        )
        or {}
    )


async def addCategory(
    ctx: discord.ApplicationContext,
    region: str,
    shortname: str,
    memberRole: discord.Role,
):
    guild = ctx.guild
    if guild is None:
        return
    belowCrewData = getBelowCrewData(shortname)
    prefixes = (
        utils.getDbField(constants.configCollection, "crew_region", "prefixes") or {}
    )
    categoryPrefixes = prefixes.get("category") if isinstance(prefixes, dict) else {}
    belowCategoryChannel = guild.get_channel(belowCrewData["category_id"])
    overwrites = getOverwritesFromDust(ctx, guild, memberRole)
    if not isinstance(categoryPrefixes, dict) or belowCategoryChannel is None:
        return
    name = constants.categoryCommon + " ".join(shortname.upper())
    name = categoryPrefixes[region] + name
    return await guild.create_category_channel(
        name, position=belowCategoryChannel.position - 1, overwrites=overwrites
    )


def getPermissionsAndPositions(ctx: discord.ApplicationContext) -> dict:
    crewData = constants.crewCollection.find_one()
    if not isinstance(crewData, dict):
        return {"permissions": None, "positions": None}
    memberRoleId, adminRoleId, leaderRoleId = (
        crewData["member"],
        crewData["admin"],
        crewData["leader"],
    )
    memberRole, adminRole, leaderRole = (
        utils.getRole(ctx, memberRoleId),
        utils.getRole(ctx, adminRoleId),
        utils.getRole(ctx, leaderRoleId),
    )
    if memberRole is None or adminRole is None or leaderRole is None:
        return {"permissions": None, "positions": None}
    return {
        "permissions": {
            "member": memberRole.permissions,
            "admin": adminRole.permissions,
            "leader": leaderRole.permissions,
        },
        "positions": {
            "member": memberRole.position + 1,
            "admin": adminRole.position + 1,
            "leader": leaderRole.position + 1,
        },
    }


async def createAndMoveRole(
    guild: discord.Guild, roleName: str, permissions: discord.Permissions, position: int
):
    memberRole = await guild.create_role(
        name=roleName, permissions=permissions, mentionable=True, hoist=True
    )
    return await memberRole.edit(position=position)


async def addRoles(ctx: discord.ApplicationContext, shortname: str, longname: str):
    memberRoleName = longname.capitalize()
    adminRoleName = shortname.capitalize() + " Admin"
    leaderRoleName = shortname.capitalize() + " Leader"
    guild = ctx.guild
    permissions = getPermissionsAndPositions(ctx)["permissions"]
    positions = getPermissionsAndPositions(ctx)["positions"]
    if permissions is None or guild is None or positions is None:
        return
    memberRole = await createAndMoveRole(
        guild, memberRoleName, permissions["member"], positions["member"]
    )
    adminRole = await createAndMoveRole(
        guild, adminRoleName, permissions["admin"], positions["admin"]
    )
    leaderRole = await createAndMoveRole(
        guild, leaderRoleName, permissions["leader"], positions["leader"]
    )
    return memberRole, adminRole, leaderRole


async def addChannels(
    ctx: discord.ApplicationContext,
    shortname: str,
    region: str,
    categoryChannel: discord.CategoryChannel,
    memberRole: discord.Role,
):
    guild = ctx.guild
    if guild is None:
        return
    overwrites = getOverwritesFromDust(ctx, guild, memberRole, "CHANNEL")
    await guild.create_text_channel(
        "🅒】" + shortname + "┃chat", category=categoryChannel, overwrites=overwrites
    )
    membersChannel = await guild.create_text_channel(
        "🅜】" + shortname + "┃members", category=categoryChannel
    )
    await guild.create_text_channel(
        "🅘】" + shortname + "┃info", category=categoryChannel
    )
    await guild.create_text_channel(
        "🅟】" + shortname + "┃polls", category=categoryChannel
    )
    await guild.create_text_channel(
        "🅡】" + shortname + "┃records", category=categoryChannel
    )
    prefixes = (
        utils.getDbField(constants.configCollection, "crew_region", "prefixes") or {}
    )
    channelPrefixes = (
        prefixes.get("channel") if isinstance(prefixes, dict) else {}
    ) or {}
    leaderboardPrefixes = (
        prefixes.get("leaderboard") if isinstance(prefixes, dict) else {}
    ) or {}
    leadershipCategoryId = utils.getDbField(
        constants.configCollection, "IDs", "leadership_category_id"
    )
    leadershipCategoryId = (
        leadershipCategoryId if isinstance(leadershipCategoryId, int) else -1
    )
    leadershipCategory = guild.get_channel(leadershipCategoryId)
    leaderboardCategoryId = utils.getDbField(
        constants.configCollection, "IDs", "leaderboards_category_id"
    )
    leaderboardCategoryId = (
        leaderboardCategoryId if isinstance(leaderboardCategoryId, int) else -1
    )
    leaderboardCategory = guild.get_channel(leaderboardCategoryId)
    belowCrewData = getBelowCrewData(shortname)
    belowCrewAdminChannel = guild.get_channel(belowCrewData["admin_channel_id"])
    if (
        not isinstance(leadershipCategory, discord.CategoryChannel)
        or not isinstance(belowCrewAdminChannel, discord.TextChannel)
        or not isinstance(leaderboardCategory, discord.CategoryChannel)
    ):
        return
    adminChannel = await guild.create_text_channel(
        channelPrefixes[region] + shortname + "┃leadership",
        category=leadershipCategory,
        position=belowCrewAdminChannel.position - 1,
    )
    leaderboardChannel = await guild.create_text_channel(
        leaderboardPrefixes[region] + "-" + shortname + "-0",
        category=leaderboardCategory,
    )
    return membersChannel, adminChannel, leaderboardChannel


async def addCrew(ctx: discord.ApplicationContext, region: str, shortname: str, longname: str) -> str:
    if constants.crewCollection.find_one({"key": shortname}) != None:
        return "A crew with the same shortname already exists. That needs to be unique. You can check the shortnames by using multiple other commands. If you don't find the shortname in there, contact AdrianG98RO to check the DB directly."
    if shortname.count(" ") != 0:
        return "Shortname must not contain whispaces."
    result = await addRoles(ctx, shortname, longname)
    if result is None:
        return "Error in adding roles..."
    memberRole, adminRole, leaderRole = result
    if memberRole is None or adminRole is None or leaderRole is None:
        return "Error in creating roles..."
    categoryChannel = await addCategory(ctx, region, shortname, memberRole)
    if categoryChannel is None:
        return "Error in creating the category channel..."
    result = await addChannels(ctx, shortname, region, categoryChannel, memberRole)
    if result is None:
        return "Error in adding channels..."
    membersChannel, adminChannel, leaderboardChannel = result
    constants.crewCollection.insert_one(
        {
            "key": shortname,
            "admin": adminRole.id,
            "member": memberRole.id,
            "leader": leaderRole.id,
            "leaderboard_id": leaderboardChannel.id,
            "members_channel_id": membersChannel.id,
            "admin_channel_id": adminChannel.id,
            "category_id": categoryChannel.id,
            "name": longname
        }
    )
    constants.configCollection.update_one(
        {"key": "crews"}, {"$push": {"value": shortname}}
    )
    constants.configCollection.update_one(
        {"key": "crew_region"}, {"$push": {f"value.{region}": shortname}}
    )
    constants.vacanciesCollection.update_one(
        {}, {"$set": {shortname: {"current": 0, "next": 0}}}
    )
    await updateVacancies(ctx, shortname)
    return f"Crew with shortname={shortname} and longname={longname} was successfully created, with entries in the DB, channels, category and roles. Feel free to use other commands on it from now on."


async def deleteEntity(crewData: dict, key: str, getFunction):
    id = crewData[key]
    channelOrCategoryOrRole = getFunction(id)
    if channelOrCategoryOrRole is None:
        return
    if isinstance(channelOrCategoryOrRole, discord.CategoryChannel):
        for channel in channelOrCategoryOrRole.channels:
            await channel.delete()
    await channelOrCategoryOrRole.delete()


async def deleteChannelsAndCategoryAndRoles(guild: discord.Guild, crewData: dict):
    await deleteEntity(crewData, "category_id", guild.get_channel)
    await deleteEntity(crewData, "leaderboard_id", guild.get_channel)
    await deleteEntity(crewData, "admin_channel_id", guild.get_channel)
    await deleteEntity(crewData, "admin", guild.get_role)
    await deleteEntity(crewData, "leader", guild.get_role)
    await deleteEntity(crewData, "member", guild.get_role)


async def deleteMoves(ctx: discord.ApplicationContext, shortname: str):
    moves = list(
        constants.movesCollection.find(
            {"$or": [{"crew_from": shortname}, {"crew_to": shortname}]}
        )
    )
    constants.movesCollection.delete_many(
        {"$or": [{"crew_from": shortname}, {"crew_to": shortname}]}
    )
    alteredCrews = set()
    for move in moves:
        if move["crew_from"] == shortname:
            await deleteMovementFromMessage(ctx, move["crew_from"], "OUT")
            alteredCrews.add(move["crew_from"])
        else:
            await deleteMovementFromMessage(ctx, move["crew_to"], "IN")
            alteredCrews.add(move["crew_to"])
    for crew in alteredCrews:
        await updateVacancies(ctx, crew)
    await updateVacancies(ctx, utils.getCrewNames(constants.configCollection)[0])


async def removeCrew(ctx: discord.ApplicationContext, shortname: str):
    crewData = constants.crewCollection.find_one({"key": shortname})
    if not isinstance(crewData, dict):
        return "Crew not in the dn..."
    guild = ctx.guild
    if not isinstance(guild, discord.Guild):
        return
    await deleteChannelsAndCategoryAndRoles(guild, crewData)
    constants.vacanciesCollection.update_one({}, {"$unset": {shortname: ""}})
    constants.multipleAccountsCollection.delete_one({"key": shortname})
    constants.configCollection.update_one(
        {"key": "crews"}, {"$pull": {"value": shortname}}
    )
    constants.configCollection.update_one(
        {"key": "crew_region"},
        {
            "$pull": {
                "value.EU": shortname,
                "value.US": shortname,
                "value.AUS/JPN": shortname,
            }
        },
    )
    constants.crewCollection.delete_one({"key": shortname})
    await deleteMoves(ctx, shortname)
    return f"All good. Crew {shortname} was deleted from DB, as well as channels and roles."
