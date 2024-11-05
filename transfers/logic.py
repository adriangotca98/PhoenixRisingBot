import discord
import constants
import utils
from members import logic as members_logic

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
    message = await utils.getMessage(
        ctx, crewData, messageIdKey, "members_channel_id", initialMessage
    )
    await updateMovementsMessage(ctx, message, crewName, inOrOut)

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
        outMessage = await utils.getMessage(
            ctx, crewFromData, "out_message_id", "members_channel_id", "**OUT:**"
        )
        await updateMovementsMessage(ctx, outMessage, crewFrom, "OUT")
    crewToData = constants.crewCollection.find_one({"key": crewTo}, {"_id": 0})
    if crewToData is not None:
        inMessage = await utils.getMessage(
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
            await members_logic.getPlayersResponse(ctx, crew)
    return "All good"

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
