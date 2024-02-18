from imp import new_module
import discord
from pymongo import MongoClient, collection
import time

configFile = open("config.txt", "r")
config = configFile.read()
username = config.split("\n")[0]
mongo_password = config.split("\n")[1]
client = MongoClient(f"mongodb+srv://{username}:{mongo_password}@phoenixrisingcluster.p2zno6x.mongodb.net"
                     f"/?retryWrites=true"
                     f"&w=majority")
crewCollection = client.get_database("Fawkes").get_collection("crewData")
configCollection = client.get_database("Fawkes").get_collection("configData")
multipleAccountsCollection = client.get_database("Fawkes").get_collection("multipleAccountsData")
movesCollection = client.get_database("Fawkes").get_collection("movesData")
vacanciesCollection = client.get_database("Fawkes").get_collection("vacanciesData")


def getDbField(mongoCollection: collection.Collection, key: str, subkey: str):
    entry = mongoCollection.find_one({"key": key}, {"_id": 0, subkey: 1})
    if entry is None:
        return None
    return entry[subkey]


scores = {}
crewRegionEntry = configCollection.find_one({"key": "crew_region"}, {"_id": 0, "value": 1})
crewRegionEntry = crewRegionEntry if crewRegionEntry is not None else {}
crewRegion = getDbField(configCollection, "crew_region", "value") or {}
discord_bot_token = getDbField(configCollection, "discord_token", "value") or ""
risingServerId = getDbField(configCollection, "IDs", 'rising_server_id') or -1
loggingChannelId = getDbField(configCollection, "IDs", 'logging_channel_id') or -1
hallChannelId = getDbField(configCollection, "IDs", 'hall_channel_id') or -1
vacanciesChannelId = getDbField(configCollection, "IDs", 'vacancies_channel_id') or -1
vacanciesMessageId = getDbField(configCollection, "IDs", 'vacancies_message_id') or -1
communityMemberRoleName = getDbField(configCollection, "IDs", 'community_member_role_name') or ""

def getCrewNames():
    crewNames = getDbField(configCollection, "crews", "value")
    if crewNames is None:
        return []
    crewNames.sort()
    return crewNames

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
    crewNames = getCrewNames()
    if crewNames is None:
        return
    for crew in crewNames:
        channelId = getDbField(crewCollection, crew, 'leaderboard_id') or 0
        channel = await bot.fetch_channel(channelId)
        if not isinstance(channel, discord.TextChannel):
            continue
        scores[crew] = computeScoreFromChannelName(channel.name)


def computeScoreFromChannelName(name: str):
    number = ''
    for char in name:
        if char.isnumeric():
            number += char
    return int(number)


def getScoreWithSeparator(intScore: int):
    scoreWithSeparator = ''
    while intScore > 0:
        number = str(intScore % 1000)
        while len(number) < 3:
            number = '0' + number
        scoreWithSeparator = '’' + number + scoreWithSeparator
        intScore //= 1000
    while scoreWithSeparator[0] == '0' or scoreWithSeparator[0] == '’':
        scoreWithSeparator = scoreWithSeparator[1:]
    return scoreWithSeparator


async def addOrRemoveRoleAndUpdateMultiple(ctx: discord.ApplicationContext, player: discord.Member, transfer: dict, crewName: str, op: str):
    numberOfAccounts = transfer['number_of_accounts']
    crewRoleName = str(getDbField(crewCollection, crewName, 'member'))
    crewRole = getRole(ctx, crewRoleName)
    if crewRole is None:
        return
    multipleEntry = multipleAccountsCollection.find_one({"key": crewName}) or {}
    if op == 'ADD':
        currentMultiple = 0
        if player.get_role(crewRole.id):
            currentMultiple = multipleEntry[str(player.id)] or 1
        newMultiple = currentMultiple + numberOfAccounts
        if newMultiple > 1:
            multipleAccountsCollection.update_one({"key": crewName}, {"$set": {str(player.id): newMultiple}}, upsert=True)
        await player.add_roles(crewRole)
    else:
        currentMultiple = multipleEntry[str(player.id)] or 1
        if currentMultiple - numberOfAccounts <= 1:
            multipleAccountsCollection.update_one({"key": crewName}, {"$unset": {str(player.id): ""}})
            if currentMultiple - numberOfAccounts == 0:
                await player.remove_roles(crewRole)
        else:
            multipleAccountsCollection.update_one({"key": crewName}, {"$set": {str(player.id): currentMultiple - numberOfAccounts}})


async def makeTransfers(ctx: discord.ApplicationContext):
    currentSeason = getCurrentSeason()
    if ctx.guild is None:
        return "Something is terribly wrong. Contact server admins."
    transfers = list(movesCollection.find({"season": currentSeason}))
    crewsToUpdateMembers = set()
    for transfer in transfers:
        print(f"Processing {transfer}")
        try:
            player = await ctx.guild.fetch_member(transfer['player'])
        except (discord.Forbidden, discord.HTTPException):
            movesCollection.delete_many({"player": transfer['player']})
            continue
        await addOrRemoveRoleAndUpdateMultiple(ctx, player, transfer, transfer['crew_from'], 'REMOVE')
        await addOrRemoveRoleAndUpdateMultiple(ctx, player, transfer, transfer['crew_to'], 'ADD')
        if transfer['crew_to'] == "Out of family":
            shouldKick = transfer['should_kick'] or False
            if shouldKick:
                await player.kick(reason="Kicked by Fawkes via transfer")
            else:
                communityMemberRole = getRole(ctx, communityMemberRoleName)
                if communityMemberRole is not None:
                    await player.add_roles(communityMemberRole)
        movesCollection.delete_one(transfer)
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
    channelId = getDbField(crewCollection, crewName, 'leaderboard_id') or -1
    channel = await ctx.bot.fetch_channel(channelId)
    if not isinstance(channel, discord.TextChannel):
        return
    channelName = channel.name
    newChannelName = channelName.strip("0123456789'`’") + getScoreWithSeparator(int(score))
    await channel.edit(name=newChannelName)
    scores[crewName] = int(score)
    await reorderChannels(ctx, scores, crewName)


async def reorderChannels(ctx: discord.ApplicationContext, scoresDict: dict, crewName: str):
    sortedScores = dict(sorted(scoresDict.items(), key=lambda item: item[1], reverse=True))
    channelId = getDbField(crewCollection, crewName, 'leaderboard_id') or -1
    channel = await ctx.bot.fetch_channel(channelId)
    if list(sortedScores.keys())[0] == crewName:
        if isinstance(channel, discord.TextChannel):
            await channel.move(beginning=True)
        return
    lastKey = ""
    for key in sortedScores:
        if key == crewName:
            aboveChannelId = getDbField(crewCollection, lastKey, 'leaderboard_id')
            if aboveChannelId is None:
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
        crewCollection.update_one({"key": key}, {"$set": {keyToSet: message.id}})
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


def getMembers(guild: discord.Guild, crewName, adminRoleName, leaderRoleName, memberRoleName, multipleAccountsIds,
               multipleAccountsData):
    response = []
    for member in guild.members:
        roleNames = set([role.name for role in member.roles])
        memberStruct = Member(False, False, member.id, member.display_name, 0)
        memberId = str(member.id)
        if adminRoleName in roleNames:
            memberStruct.admin = True
        if leaderRoleName in roleNames:
            memberStruct.leader = True
        if memberRoleName in roleNames:
            response.append(memberStruct)
        if memberId in multipleAccountsIds:
            if memberRoleName in roleNames:
                for i in range(multipleAccountsData[memberId] - 1):
                    newMemberStruct = Member(False, False, member.id, member.display_name, i + 2)
                    response.append(newMemberStruct)
            else:
                multipleAccountsCollection.update_one({"key": crewName}, {"$unset": {memberId: ""}})
    return response


async def getPlayersResponse(ctx: discord.ApplicationContext, key: str):
    multipleAccountsData = multipleAccountsCollection.find_one({"key": key}, {"_id": 0})
    if multipleAccountsData is not None:
        multipleAccountsIds = [key for key in multipleAccountsData if key != 'key']
    else:
        multipleAccountsIds = []
    crewData = crewCollection.find_one({"key": key}, {"_id": 0}) or {}
    crewName = getDbField(crewCollection, key, 'member') or ""
    message = await getMessage(ctx, crewData, "message_id", "members_channel_id",
                               "**__Members for " + crewName.upper() + "__**")
    memberRoleName = getDbField(crewCollection, key, 'member') or ""
    adminRoleName = getDbField(crewCollection, key, 'admin') or ""
    leaderRoleName = getDbField(crewCollection, key, 'leader') or ""
    guild = ctx.guild
    if guild is None:
        return
    roleFound = False
    for role in guild.roles:
        if role.name == memberRoleName:
            roleFound = True
    if not roleFound:
        return ("Role not found on the server! Try again and change the name to the exact "
                "name of the role you want info for!")
    response = getMembers(guild, crewName, adminRoleName, leaderRoleName, memberRoleName, multipleAccountsIds,
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
    currentSeason = getCurrentSeason()
    currentSeasonCount = len(members_list)
    vacanciesEntry = vacanciesCollection.find_one({}) or {}
    if crew_name == 'New to family' or crew_name == 'Out of family':
        return
    if currentSeasonCount == 0:
        if crew_name in vacanciesEntry:
            currentSeasonCount = vacanciesEntry[crew_name]['current']
        else:
            currentSeasonCount = 0
    nextSeasonCount = currentSeasonCount
    for move in list(movesCollection.find({"crew_to": crew_name, "season": currentSeason + 1})):
        nextSeasonCount += move['number_of_accounts']
    for move in list(movesCollection.find({"crew_from": crew_name, "season": currentSeason + 1})):
        nextSeasonCount -= move['number_of_accounts']
    vacanciesCollection.update_one({}, {"$set": {crew_name: {"current": currentSeasonCount, "next": nextSeasonCount}}})
    if crew_name in getCrewNames():
        vacanciesEntry[crew_name]['current'] = currentSeasonCount
        vacanciesEntry[crew_name]['next'] = nextSeasonCount
    messageContent = "**__Latest Crew Vacancies__**\n\n"
    for region in crewRegion.keys():
        messageContent += f"**__{region} Crews__**\n\n"
        for crew_name in crewRegion[region]:
            if crew_name not in vacanciesEntry.keys():
                continue
            messageContent += (f"**{crew_name.capitalize()}**\n{vacanciesEntry[crew_name]['current']}/30 Current Season"
                               f"\n{vacanciesEntry[crew_name]['next']}/30 Next Season\n")
        messageContent += "\n"
    guild = ctx.guild
    if guild is not None:
        channel = await guild.fetch_channel(vacanciesChannelId)
        try:
            if vacanciesMessageId is not None and isinstance(channel, discord.TextChannel):
                message = await channel.fetch_message(vacanciesMessageId)
                await message.edit(content=messageContent)
            elif isinstance(channel, discord.TextChannel):
                message = await channel.send(messageContent)
                configCollection.update_one({"key": "IDs"}, {"$set": {"vacancies_message_id": message.id}})
        except discord.errors.NotFound:
            if isinstance(channel, discord.TextChannel):
                message = await channel.send(messageContent)
                configCollection.update_one({"key": "IDs"}, {"$set": {"vacancies_message_id": message.id}})


async def deleteMovementFromMessage(ctx: discord.ApplicationContext, crewName: str, inOrOut: str):
    crewData = crewCollection.find_one({"key": crewName})
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
        if guild.id == risingServerId:
            print("Doing " + op + " for user: " + user.name + " in the server named: " + guild.name)
            if op == 'kick':
                await guild.kick(user, reason=reason)
            elif op == 'ban':
                await guild.ban(user, reason=reason, delete_message_days=0)
            elif op == 'unban':
                await guild.unban(user, reason=reason)


def processMultiple(user: discord.Member, crewName: str, numberOfAccounts: int):
    memberRoleName = getDbField(crewCollection, crewName, 'member')
    roles = user.roles
    roleFound = False
    for role in roles:
        if role.name == memberRoleName:
            roleFound = True
            break
    if not roleFound:
        return "User does not have crew role! Add crew role and try again."
    memberId = str(user.id)
    if numberOfAccounts != 1:
        multipleAccountsCollection.find_one_and_update({"key": crewName}, {"$set": {memberId: numberOfAccounts}},
                                                       upsert=True)
    else:
        multipleAccountsCollection.find_one_and_update({"key": crewName}, {"$unset": {memberId: ""}})
    return "Multiple accounts recorded!"


def getRole(ctx: discord.ApplicationContext, roleName: str):
    if ctx.guild is None:
        return None
    for role in ctx.guild.roles:
        if role.name == roleName:
            return role
    return None


def getCurrentSeason():
    return int((time.time() - (getDbField(configCollection, 'time', 'value') or 0)) / 60 / 60 / 24 / 7 / 2) + 166


async def processTransfer(ctx: discord.ApplicationContext, player: discord.Member, crewFrom: str, crewTo: str,
                          numberOfAccounts: int, season: int, pingAdmin: bool, shouldKick: bool):
    if crewFrom == "New to family" and crewTo == "Out of family":
        return "A player can't be new to family and going out of family at the same time"
    if crewFrom == crewTo:
        return "A move can't take place within the same crew."
    if crewTo == "Out of family" and shouldKick is None:
        return "Set should_kick for this kind of move."
    if season < getCurrentSeason():
        return "Transfers can only happen in the future or in the current season"
    message = await processMovement(ctx, crewFrom, crewTo, player, numberOfAccounts, season, pingAdmin, shouldKick)
    return message


def checkRole(ctx: discord.ApplicationContext, player: discord.Member, crewName: str):
    crewData = crewCollection.find_one({"key": crewName}, {"_id": 0, "member": 1})
    if crewData is None:
        return False
    roleName = crewData['member']
    role = getRole(ctx, roleName)
    if role is None or player.get_role(role.id) is None:
        return False
    return True


def checkHistory(ctx: discord.ApplicationContext, player: discord.Member, crewName: str, season: int):
    movesData = list(movesCollection.find({"player": player.id, "season": {"$lt": season}}))
    movesData.sort(key=lambda elem: elem['season'])
    if len(movesData) != 0:
        lastMove = movesData[-1]
        if lastMove['crew_to'] != crewName:
            return (False,
                    f"I looked at this player history of movements and from what I can see, he will NOT be in "
                    f"**{getDbField(crewCollection, crewName, 'member')}** at the time of the transfer. "
                    f"Last move is registered to {lastMove['crew_to']} in season {lastMove['season']}. "
                    f"If your move is before that you'll have to redo the path till then so we don't risk missing links"
                    f" between seasons. Talk with <@308561593858392065> about how to do this.")
        return True, "history"
    hasRole = checkRole(ctx, player, crewName)
    if not hasRole:
        return False, "The player does not have the crew role. Add the role and try again."
    return True, "crew_role"


def checkForNumberOfAccounts(player: discord.Member, crewName: str, season: int, numberOfAccountsToMoveNext: int):
    multipleData = multipleAccountsCollection.find_one({"key": crewName}, {"_id": 0, str(player.id): 1})
    if multipleData is None or str(player.id) not in multipleData.keys():
        numberOfAccountsAvailableToMove = 1
    else:
        numberOfAccountsAvailableToMove = multipleData[str(player.id)]
    movesBeforeTheSeason = movesCollection.find({"player": player.id, "crew_from": crewName, "season": {"$lt": season}})
    for move in movesBeforeTheSeason:
        numberOfAccountsAvailableToMove -= move['number_of_accounts'] or 1
    existingMovesData = movesCollection.find({"player": player.id, "crew_from": crewName})
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
    movementData = movesCollection.find_one({"player": player.id, "crew_from": crewFrom, "crew_to": crewTo})
    if movementData is not None:
        movesCollection.delete_one({"player": player.id, "crew_from": crewFrom, "crew_to": crewTo})
    objectToInsert = {"player": player.id, "crew_from": crewFrom, "crew_to": crewTo,
                      "number_of_accounts": numberOfAccounts, "season": season}
    if shouldKick is not None and crewTo == "Out of family":
        objectToInsert["should_kick"] = True
    movesCollection.insert_one(objectToInsert)
    crewFromData = crewCollection.find_one({"key": crewFrom}, {"_id": 0})
    if crewFromData is not None:
        outMessage = await getMessage(ctx, crewFromData, 'out_message_id', "members_channel_id", "**OUT:**")
        await updateMovementsMessage(ctx, outMessage, crewFrom, 'OUT')
    crewToData = crewCollection.find_one({"key": crewTo}, {"_id": 0})
    if crewToData is not None:
        inMessage = await getMessage(ctx, crewToData, "in_message_id", "members_channel_id", "**IN:**")
        await updateMovementsMessage(ctx, inMessage, crewTo, "IN")
    await updateVacancies(ctx, crewFrom)
    await updateVacancies(ctx, crewTo)
    await sendMessageToAdminChat(ctx, crewTo, player, "confirm", "to", pingAdmin, season, numberOfAccounts)
    await sendMessageToAdminChat(ctx, crewFrom, player, "confirm", "from", pingAdmin, season, numberOfAccounts)
    if season == getCurrentSeason():
        await makeTransfers(ctx)
    return "Transfer processed successfully"


async def sendMessageToAdminChat(ctx: discord.ApplicationContext, crew: str, player: discord.Member,
                                 confirmOrCancel: str, toOrFrom: str, pingAdmin: bool, season: int,
                                 numberOfAccounts: int):
    if not pingAdmin:
        return
    crewData = crewCollection.find_one({"key": crew}, {"admin_channel_id": 1, "admin": 1, "_id": 0})
    if crewData is None:
        return
    adminRole = getRole(ctx, crewData['admin'])
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
    movements = movesCollection.find({movementsKey: crewName}, {"_id": 0})
    idx = 1
    for move in movements:
        crewData = crewCollection.find_one({"key": move[crewKey]}, {"_id": 0})
        try:
            guild = ctx.guild
            if guild is not None:
                member = await guild.fetch_member(move['player'])
            else:
                member = None
        except discord.Forbidden or discord.HTTPException:
            movesCollection.delete_many({"player": move['player']})
            continue
        if member is not None:
            newMessage += f"{str(idx)}. {member.mention} "
        if crewData is None:
            newMessage += f"{move[crewKey]} in S{str(move['season'])}"
        else:
            crewRole = getRole(ctx, crewData['member'])
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
        moves = list(movesCollection.find({"player": player.id}))
        if len(moves) == 0:
            return "No moves found for this player."
        if len(moves) > 1:
            return "Too many moves found, add crew_from and crew_to and try again."
        move = moves[0]
    else:
        move = list(movesCollection.find({"player": player.id, "crew_from": crewFrom, "crew_to": crewTo}))[0]
    movesCollection.delete_one({"player": move['player']})
    await deleteMovementFromMessage(ctx, move['crew_from'], "OUT")
    await deleteMovementFromMessage(ctx, move['crew_to'], "IN")
    await updateVacancies(ctx, move['crew_from'])
    await updateVacancies(ctx, move['crew_to'])
    await sendMessageToAdminChat(ctx, move['crew_to'], player, "cancel", "to", pingAdmin, move['season'],
                                 move['number_of_accounts'])
    await sendMessageToAdminChat(ctx, move['crew_from'], player, "cancel", "from", pingAdmin, move['season'],
                                 move['number_of_accounts'])
    return f"Cancelled transfer for {player.name} from {crewFrom} to {crewTo}"


commandsList = ['ban','cancel_transfer','current_season','kick','make_transfers','members','multiple','score','transfer','unban']
commandsMessages={
    'ban': '# Banning Time!\nSelect user to ban from the server below:',
    'cancel_transfer': '# Cancel Transfer?\nIf you wish to cancel an input transfer, complete the following fields and submit:',
    'current_season': lambda: f'# Current Season\nWe are currently in season {getCurrentSeason()}',
    'kick': '# Booting Time!\nSelect user you would like to kick from the server below:',
    'make_transfers': '# Make Transfers?\nUpon confirming, Fawkes will complete all crew transfers for the current season. Are you sure?',
    'members': '# Member List Update\nChoose a crew from the list below to update its current members count:',
    'multiple': '# Multi-Account Register\nChoose a user below to change how many accounts they have in a given crew:',
    'score': '# Crew Score\nSelect a crew below to update its end of season score:',
    'transfer': lambda: f'# Player Transfer\nComplete the below fields to register an upcoming player transfer (please note that current season is {getCurrentSeason()}):',
    'unban': '# Undo Ban\nInput the discord name of a user you wish to lift a ban from:'
}