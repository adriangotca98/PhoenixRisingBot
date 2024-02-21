import discord
import utils
import constants


class Member:
    def __init__(self, admin: bool, leader: bool, member_id: int, name: str, multiple: int):
        self.admin = admin
        self.leader = leader
        self.member_id = member_id
        self.name = name
        self.multiple = multiple


def sortFunction(member: Member):
    if member.leader:
        return '0 ' + member.name
    if member.admin:
        return '1 ' + member.name
    return "2 " + member.name


async def init(bot: discord.Bot):
    crewNames = utils.getCrewNames(constants.configCollection)
    if crewNames is None:
        return
    for crew in crewNames:
        channelId = utils.getDbField(constants.crewCollection, crew, 'leaderboard_id') or 0
        if not isinstance(channelId, int):
            continue
        channel = await bot.fetch_channel(channelId)
        if not isinstance(channel, discord.TextChannel):
            continue
        constants.scores[crew] = utils.computeScoreFromChannelName(channel.name)


async def addOrRemoveRoleAndUpdateMultiple(ctx: discord.ApplicationContext, player: discord.Member, transfer: dict, crewName: str, op: str):
    numberOfAccounts = transfer['number_of_accounts']
    crewRoleId = utils.getDbField(constants.crewCollection, crewName, 'member')
    if not isinstance(crewRoleId, int):
        return
    crewRole = utils.getRole(ctx, crewRoleId)
    if crewRole is None:
        return
    multipleEntry = constants.multipleAccountsCollection.find_one({"key": crewName}) or {}
    if op == 'ADD':
        currentMultiple = 0
        if player.get_role(crewRole.id):
            currentMultiple = multipleEntry[str(player.id)] or 1
        newMultiple = currentMultiple + numberOfAccounts
        if newMultiple > 1:
            constants.multipleAccountsCollection.update_one({"key": crewName}, {"$set": {str(player.id): newMultiple}}, upsert=True)
        await player.add_roles(crewRole)
    else:
        currentMultiple = multipleEntry[str(player.id)] or 1
        if currentMultiple - numberOfAccounts <= 1:
            constants.multipleAccountsCollection.update_one({"key": crewName}, {"$unset": {str(player.id): ""}})
            if currentMultiple - numberOfAccounts == 0:
                await player.remove_roles(crewRole)
        else:
            constants.multipleAccountsCollection.update_one({"key": crewName}, {"$set": {str(player.id): currentMultiple - numberOfAccounts}})


async def makeTransfers(ctx: discord.ApplicationContext):
    currentSeason = utils.getCurrentSeason(constants.configCollection)
    if ctx.guild is None:
        return "Something is terribly wrong. Contact server admins."
    transfers = list(constants.movesCollection.find({"season": currentSeason}))
    crewsToUpdateMembers = set()
    for transfer in transfers:
        print(f"Processing {transfer}")
        try:
            player = await ctx.guild.fetch_member(transfer['player'])
        except (discord.Forbidden, discord.HTTPException):
            constants.movesCollection.delete_many({"player": transfer['player']})
            continue
        await addOrRemoveRoleAndUpdateMultiple(ctx, player, transfer, transfer['crew_from'], 'REMOVE')
        await addOrRemoveRoleAndUpdateMultiple(ctx, player, transfer, transfer['crew_to'], 'ADD')
        if transfer['crew_to'] == "Out of family":
            shouldKick = transfer['should_kick'] or False
            if shouldKick:
                await player.kick(reason="Kicked by Fawkes via transfer")
            else:
                if isinstance(constants.communityMemberRoleId, int):
                    communityMemberRole = utils.getRole(ctx, constants.communityMemberRoleId)
                    if communityMemberRole is not None:
                        await player.add_roles(communityMemberRole)
        constants.movesCollection.delete_one(transfer)
        await deleteMovementFromMessage(ctx, transfer['crew_from'], "OUT")
        await deleteMovementFromMessage(ctx, transfer['crew_to'], "IN")
        crewsToUpdateMembers.add(transfer['crew_from'])
        crewsToUpdateMembers.add(transfer['crew_to'])
    for crew in crewsToUpdateMembers:
        if crew not in ['New to family', 'Out of family']:
            await getPlayersResponse(ctx, crew)
    return "All good"


async def setScore(ctx: discord.ApplicationContext, crewName: str, score: str):
    print(f"Setting score {str(score)} for {crewName}")
    channelId = utils.getDbField(constants.crewCollection, crewName, 'leaderboard_id') or -1
    if not isinstance(channelId, int):
        return
    channel = await ctx.bot.fetch_channel(channelId)
    if not isinstance(channel, discord.TextChannel):
        return
    channelName = channel.name
    newChannelName = channelName.strip("0123456789'`’") + utils.getScoreWithSeparator(int(score))
    await channel.edit(name=newChannelName)
    constants.scores[crewName] = int(score)
    await reorderChannels(ctx, constants.scores, crewName)


async def reorderChannels(ctx: discord.ApplicationContext, scoresDict: dict, crewName: str):
    sortedScores = dict(sorted(scoresDict.items(), key=lambda item: item[1], reverse=True))
    channelId = utils.getDbField(constants.crewCollection, crewName, 'leaderboard_id') or -1
    if not isinstance(channelId, int):
        return
    channel = await ctx.bot.fetch_channel(channelId)
    if list(sortedScores.keys())[0] == crewName:
        if isinstance(channel, discord.TextChannel):
            await channel.move(beginning=True)
        return
    lastKey = ""
    for key in sortedScores:
        if key == crewName:
            aboveChannelId = utils.getDbField(constants.crewCollection, lastKey, 'leaderboard_id')
            if aboveChannelId is None or not isinstance(aboveChannelId, int):
                continue
            aboveChannel = await ctx.bot.fetch_channel(aboveChannelId)
            if isinstance(channel, discord.TextChannel):
                await channel.move(after=aboveChannel)
            return
        lastKey = key


async def updateMessage(ctx: discord.ApplicationContext, crewData, keyToSet, initialMessage):
    key = crewData['key']
    channelId = crewData['members_channel_id']
    channel = await ctx.bot.fetch_channel(channelId)
    if isinstance(channel, discord.TextChannel):
        message = await channel.send(initialMessage)
        constants.crewCollection.update_one({"key": key}, {"$set": {keyToSet: message.id}})
        return message
    return None


async def getMessage(ctx, crewData: dict, keyToGet: str, channelKey: str, initialMessage: str):
    if keyToGet not in crewData.keys():
        message = await updateMessage(ctx, crewData, keyToGet, initialMessage)
    else:
        channelId = crewData[channelKey]
        channel = await ctx.bot.fetch_channel(channelId)
        try:
            message = await channel.fetch_message(crewData[keyToGet])
        except discord.errors.NotFound:
            print('Message not found. Creating another one :)')
            message = await updateMessage(ctx, crewData, keyToGet, initialMessage)
    return message


def getMembers(guild: discord.Guild, crewName: str, adminRole: discord.Role, leaderRole: discord.Role, memberRole: discord.Role, multipleAccountsIds,
               multipleAccountsData):
    response = []
    
    for member in guild.members:
        memberStruct = Member(False, False, member.id, member.display_name, 0)
        memberId = str(member.id)
        if member.get_role(adminRole.id):
            memberStruct.admin = True
        if member.get_role(leaderRole.id):
            memberStruct.leader = True
        if member.get_role(memberRole.id):
            response.append(memberStruct)
        if memberId in multipleAccountsIds:
            if member.get_role(memberRole.id):
                for i in range(multipleAccountsData[memberId] - 1):
                    newMemberStruct = Member(False, False, member.id, member.display_name, i + 2)
                    response.append(newMemberStruct)
            else:
                constants.multipleAccountsCollection.update_one({"key": crewName}, {"$unset": {memberId: ""}})
    return response


async def getPlayersResponse(ctx: discord.ApplicationContext, key: str):
    multipleAccountsData = constants.multipleAccountsCollection.find_one({"key": key}, {"_id": 0})
    if multipleAccountsData is not None:
        multipleAccountsIds = [key for key in multipleAccountsData if key != 'key']
    else:
        multipleAccountsIds = []
    crewData = constants.crewCollection.find_one({"key": key}, {"_id": 0}) or {}
    memberRoleId = utils.getDbField(constants.crewCollection, key, 'member') or ""
    adminRoleId = utils.getDbField(constants.crewCollection, key, 'admin') or ""
    leaderRoleId = utils.getDbField(constants.crewCollection, key, 'leader') or ""
    if not isinstance(memberRoleId, int) or not isinstance(adminRoleId, int) or not isinstance(leaderRoleId, int):
        return
    memberRole = utils.getRole(ctx, memberRoleId)
    adminRole = utils.getRole(ctx, adminRoleId)
    leaderRole = utils.getRole(ctx, leaderRoleId)
    if memberRole is None or adminRole is None or leaderRole is None:
        return
    crewName = memberRole.name
    message = await getMessage(ctx, crewData, "message_id", "members_channel_id",
                               "**__Members for " + crewName.upper() + "__**")
    guild = ctx.guild
    if guild is None:
        return
    response = getMembers(guild, crewName, adminRole, leaderRole, memberRole, multipleAccountsIds,
                          multipleAccountsData)
    response.sort(key=sortFunction)
    await updateVacancies(ctx, key, response)

    stringResponse = '**__Members of ' + crewName.upper() + "__**\n"
    number = 1
    for member in response:
        stringResponse += str(number) + ". <@!" + str(member.member_id) + ">"
        if member.multiple:
            stringResponse += " " + str(member.multiple)
        if member.leader:
            stringResponse += " -> **Leader**"
        elif member.admin:
            stringResponse += " -> *Admin*"
        stringResponse += '\n'
        number += 1
    if message is not None:
        await message.edit(content=stringResponse)
    return "OK, all good."


async def updateVacancies(ctx: discord.ApplicationContext, crew_name: str, members_list: list = []):
    currentSeason = utils.getCurrentSeason(constants.configCollection)
    currentSeasonCount = len(members_list)
    vacanciesEntry = constants.vacanciesCollection.find_one({}) or {}
    if crew_name == 'New to family' or crew_name == 'Out of family':
        return
    if currentSeasonCount == 0:
        if crew_name in vacanciesEntry:
            currentSeasonCount = vacanciesEntry[crew_name]['current']
        else:
            currentSeasonCount = 0
    nextSeasonCount = currentSeasonCount
    for move in list(constants.movesCollection.find({"crew_to": crew_name, "season": currentSeason + 1})):
        nextSeasonCount += move['number_of_accounts']
    for move in list(constants.movesCollection.find({"crew_from": crew_name, "season": currentSeason + 1})):
        nextSeasonCount -= move['number_of_accounts']
    constants.vacanciesCollection.update_one({}, {"$set": {crew_name: {"current": currentSeasonCount, "next": nextSeasonCount}}})
    if crew_name in utils.getCrewNames(constants.configCollection):
        vacanciesEntry[crew_name]['current'] = currentSeasonCount
        vacanciesEntry[crew_name]['next'] = nextSeasonCount
    messageContent = "**__Latest Crew Vacancies__**\n\n"
    crewRegion = utils.getCrewRegion(constants.configCollection)
    for region in crewRegion.keys():
        messageContent += f"**__{region} Crews__**\n\n"
        for crew_name in crewRegion[region]:
            if crew_name not in vacanciesEntry.keys():
                continue
            messageContent += (f"**{crew_name.capitalize()}**\n{vacanciesEntry[crew_name]['current']}/30 Current Season"
                               f"\n{vacanciesEntry[crew_name]['next']}/30 Next Season\n")
        messageContent += "\n"
    guild = ctx.guild
    if guild is not None and isinstance(constants.vacanciesChannelId, int) and isinstance(constants.vacanciesMessageId, int):
        channel = await guild.fetch_channel(constants.vacanciesChannelId)
        try:
            if constants.vacanciesMessageId is not None and isinstance(channel, discord.TextChannel):
                message = await channel.fetch_message(constants.vacanciesMessageId)
                await message.edit(content=messageContent)
            elif isinstance(channel, discord.TextChannel):
                message = await channel.send(messageContent)
                constants.configCollection.update_one({"key": "IDs"}, {"$set": {"vacancies_message_id": message.id}})
        except discord.errors.NotFound:
            if isinstance(channel, discord.TextChannel):
                message = await channel.send(messageContent)
                constants.configCollection.update_one({"key": "IDs"}, {"$set": {"vacancies_message_id": message.id}})


async def deleteMovementFromMessage(ctx: discord.ApplicationContext, crewName: str, inOrOut: str):
    crewData = constants.crewCollection.find_one({"key": crewName})
    if crewData is None:
        return
    if inOrOut == "IN":
        messageIdKey = 'in_message_id'
        initialMessage = "Players Joining:"
    else:
        messageIdKey = 'out_message_id'
        initialMessage = "Players Leaving:"
    message = await getMessage(ctx, crewData, messageIdKey, 'members_channel_id', initialMessage)
    await updateMovementsMessage(ctx, message, crewName, inOrOut)


async def kickOrBanOrUnban(user: discord.Member, op: str, bot: discord.Bot, reason: str | None = None):
    for guild in bot.guilds:
        if guild.id == constants.risingServerId:
            print("Doing " + op + " for user: " + user.name + " in the server named: " + guild.name)
            if op == 'kick':
                await guild.kick(user, reason=reason)
            elif op == 'ban':
                await guild.ban(user, reason=reason, delete_message_days=0)
            elif op == 'unban':
                await guild.unban(user, reason=reason)


def processMultiple(user: discord.Member, crewName: str, numberOfAccounts: int):
    memberRoleId = utils.getDbField(constants.crewCollection, crewName, 'member')
    if not isinstance(memberRoleId, int):
        return "Database error. Contact @AdrianG98RO for fixing it."
    if not user.get_role(memberRoleId):
        return "User does not have crew role! Add crew role and try again."
    memberId = str(user.id)
    if numberOfAccounts != 1:
        constants.multipleAccountsCollection.find_one_and_update({"key": crewName}, {"$set": {memberId: numberOfAccounts}},
                                                       upsert=True)
    else:
        constants.multipleAccountsCollection.find_one_and_update({"key": crewName}, {"$unset": {memberId: ""}})
    return "Multiple accounts recorded!"


async def processTransfer(ctx: discord.ApplicationContext, player: discord.Member, crewFrom: str, crewTo: str,
                          numberOfAccounts: int, season: int, pingAdmin: bool, shouldKick: bool):
    if crewFrom == "New to family" and crewTo == "Out of family":
        return "A player can't be new to family and going out of family at the same time"
    if crewFrom == crewTo:
        return "A move can't take place within the same crew."
    if crewTo == "Out of family" and shouldKick is None:
        return "Set should_kick for this kind of move."
    if season < utils.getCurrentSeason(constants.configCollection):
        return "Transfers can only happen in the future or in the current season"
    message = await processMovement(ctx, crewFrom, crewTo, player, numberOfAccounts, season, pingAdmin, shouldKick)
    return message


def checkRole(ctx: discord.ApplicationContext, player: discord.Member, crewName: str):
    crewData = constants.crewCollection.find_one({"key": crewName}, {"_id": 0, "member": 1})
    if crewData is None:
        return False
    roleName = crewData['member']
    role = utils.getRole(ctx, roleName)
    if role is None or player.get_role(role.id) is None:
        return False
    return True


def checkHistory(ctx: discord.ApplicationContext, player: discord.Member, crewName: str, season: int):
    movesData = list(constants.movesCollection.find({"player": player.id, "season": {"$lt": season}}))
    movesData.sort(key=lambda elem: elem['season'])
    if len(movesData) != 0:
        lastMove = movesData[-1]
        if lastMove['crew_to'] != crewName:
            return (False,
                    f"I looked at this player history of movements and from what I can see, he will NOT be in "
                    f"**{crewName}** at the time of the transfer. "
                    f"Last move is registered to {lastMove['crew_to']} in season {lastMove['season']}. "
                    f"If your move is before that you'll have to redo the path till then so we don't risk missing links"
                    f" between seasons. Talk with <@308561593858392065> about how to do this.")
        return True, "history"
    hasRole = checkRole(ctx, player, crewName)
    if not hasRole:
        return False, "The player does not have the crew role. Add the role and try again."
    return True, "crew_role"


def checkForNumberOfAccounts(player: discord.Member, crewName: str, season: int, numberOfAccountsToMoveNext: int):
    multipleData = constants.multipleAccountsCollection.find_one({"key": crewName}, {"_id": 0, str(player.id): 1})
    if multipleData is None or str(player.id) not in multipleData.keys():
        numberOfAccountsAvailableToMove = 1
    else:
        numberOfAccountsAvailableToMove = multipleData[str(player.id)]
    movesBeforeTheSeason = constants.movesCollection.find({"player": player.id, "crew_from": crewName, "season": {"$lt": season}})
    for move in movesBeforeTheSeason:
        numberOfAccountsAvailableToMove -= move['number_of_accounts'] or 1
    existingMovesData = constants.movesCollection.find({"player": player.id, "crew_from": crewName})
    for existingMove in existingMovesData:
        numAccounts = existingMove['number_of_accounts'] if 'number_of_accounts' in existingMove.keys() else 1
        numberOfAccountsAvailableToMove -= numAccounts
    return numberOfAccountsAvailableToMove >= numberOfAccountsToMoveNext


async def processMovement(ctx: discord.ApplicationContext, crewFrom: str, crewTo: str, player: discord.Member,
                          numberOfAccounts: int, season: int, pingAdmin: bool, shouldKick: bool) -> str:
    historyCheck = checkHistory(ctx, player, crewFrom, season)
    if not historyCheck[0]:
        return historyCheck[1]
    if not checkForNumberOfAccounts(player, crewFrom, season, numberOfAccounts):
        return ("The player has too many accounts registered to transfer with this transfer included. "
                "Check the multiple or remove from the existing transfers for this player first.")
    movementData = constants.movesCollection.find_one({"player": player.id, "crew_from": crewFrom, "crew_to": crewTo})
    if movementData is not None:
        constants.movesCollection.delete_one({"player": player.id, "crew_from": crewFrom, "crew_to": crewTo})
    objectToInsert = {"player": player.id, "crew_from": crewFrom, "crew_to": crewTo,
                      "number_of_accounts": numberOfAccounts, "season": season}
    if shouldKick is not None and crewTo == "Out of family":
        objectToInsert["should_kick"] = True
    constants.movesCollection.insert_one(objectToInsert)
    crewFromData = constants.crewCollection.find_one({"key": crewFrom}, {"_id": 0})
    if crewFromData is not None:
        outMessage = await getMessage(ctx, crewFromData, 'out_message_id', "members_channel_id", "**OUT:**")
        await updateMovementsMessage(ctx, outMessage, crewFrom, 'OUT')
    crewToData = constants.crewCollection.find_one({"key": crewTo}, {"_id": 0})
    if crewToData is not None:
        inMessage = await getMessage(ctx, crewToData, "in_message_id", "members_channel_id", "**IN:**")
        await updateMovementsMessage(ctx, inMessage, crewTo, "IN")
    await updateVacancies(ctx, crewFrom)
    await updateVacancies(ctx, crewTo)
    await sendMessageToAdminChat(ctx, crewTo, player, "confirm", "to", pingAdmin, season, numberOfAccounts)
    await sendMessageToAdminChat(ctx, crewFrom, player, "confirm", "from", pingAdmin, season, numberOfAccounts)
    if season == utils.getCurrentSeason(constants.configCollection):
        await makeTransfers(ctx)
    return "Transfer processed successfully"


async def sendMessageToAdminChat(ctx: discord.ApplicationContext, crew: str, player: discord.Member,
                                 confirmOrCancel: str, toOrFrom: str, pingAdmin: bool, season: int,
                                 numberOfAccounts: int):
    if not pingAdmin:
        return
    crewData = constants.crewCollection.find_one({"key": crew}, {"admin_channel_id": 1, "admin": 1, "_id": 0})
    if crewData is None:
        return
    adminRole = utils.getRole(ctx, crewData['admin'])
    if adminRole is None:
        return
    message = ""
    if confirmOrCancel == "confirm" and ctx.author:
        message = (f"{adminRole.mention},\n{ctx.author.mention} confirmed that {player.mention} will be moving "
                   f"{toOrFrom} your crew in S{season} with {numberOfAccounts} account") + (
            "s." if numberOfAccounts > 1 else ".")
    elif ctx.author:
        message = (f"{adminRole.mention},\n{ctx.author.mention} has just canceled a scheduled move of {player.mention} "
                   f"{toOrFrom} your crew in S{season} with {numberOfAccounts} account") + (
            "s." if numberOfAccounts > 1 else ".")
    channel = await ctx.bot.fetch_channel(crewData['admin_channel_id'])
    if isinstance(channel, discord.TextChannel):
        await channel.send(message)


async def updateMovementsMessage(ctx: discord.ApplicationContext, message, crewName, inOrOut):
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
                member = await guild.fetch_member(move['player'])
            else:
                member = None
        except discord.Forbidden or discord.HTTPException:
            constants.movesCollection.delete_many({"player": move['player']})
            continue
        if member is not None:
            newMessage += f"{str(idx)}. {member.mention} "
        if crewData is None:
            newMessage += f"{move[crewKey]} in S{str(move['season'])}"
        else:
            crewRole = utils.getRole(ctx, crewData['member'])
            numberOfAccounts = move['number_of_accounts']
            newMessage += (f'{"from" if inOrOut == "IN" else "to"} {crewRole.mention if crewRole is not None else ""}'
                           f'{f" with {numberOfAccounts} accounts" if numberOfAccounts > 1 else ""} in '
                           f'S{str(move["season"])}')
        newMessage += '\n'
        idx += 1
    await message.edit(newMessage)


async def unregisterTransfer(ctx: discord.ApplicationContext, player: discord.Member, crewFrom, crewTo, pingAdmin=True):
    if crewTo != crewFrom and (crewTo is None or crewFrom is None):
        return "if you give one of crew_from and crew_to, you must give the other as well."
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
        move = list(constants.movesCollection.find({"player": player.id, "crew_from": crewFrom, "crew_to": crewTo}))[0]
    constants.movesCollection.delete_one({"player": move['player']})
    await deleteMovementFromMessage(ctx, move['crew_from'], "OUT")
    await deleteMovementFromMessage(ctx, move['crew_to'], "IN")
    await updateVacancies(ctx, move['crew_from'])
    await updateVacancies(ctx, move['crew_to'])
    await sendMessageToAdminChat(ctx, move['crew_to'], player, "cancel", "to", pingAdmin, move['season'],
                                 move['number_of_accounts'])
    await sendMessageToAdminChat(ctx, move['crew_from'], player, "cancel", "from", pingAdmin, move['season'],
                                 move['number_of_accounts'])
    return f"Cancelled transfer for {player.name} from {crewFrom} to {crewTo}"


async def addCrew(ctx: discord.ApplicationContext, category: discord.CategoryChannel, region: str, shortname: str):
    pass