from typing import List
import discord
from pymongo import MongoClient, collection
import time

configFile = open("config.txt", "r")
config = configFile.read()
username = config.split("\n")[0]
password = config.split("\n")[1]
client = MongoClient(f"mongodb+srv://{username}:{password}@phoenixrisingcluster.p2zno6x.mongodb.net/?retryWrites=true&w=majority")
crewCollection = client.get_database("Fawkes").get_collection("crewData")
configCollection = client.get_database("Fawkes").get_collection("configData")
multipleAccountsCollection = client.get_database("Fawkes").get_collection("multipleAccountsData")
movesCollection = client.get_database("Fawkes").get_collection("movesData")
vacanciesCollection = client.get_database("Fawkes").get_collection("vacanciesData")

def getDbField(collection: collection.Collection, key: str, subkey: str):
    entry = collection.find_one({"key": key}, {"_id": 0, subkey: 1})
    if entry is None:
        return None
    return entry[subkey]

scores = {}
crewRegionEntry = configCollection.find_one({"key": "crew_region"}, {"_id": 0, "value": 1})
crewRegionEntry = crewRegionEntry if crewRegionEntry != None else {}
crewRegion = getDbField(configCollection, "crew_region", "value") or {}
discord_bot_token = getDbField(configCollection, "discord_token", "value") or ""
risingServerId = getDbField(configCollection, "IDs", 'rising_server_id') or -1
knowingServerId = getDbField(configCollection, "IDs", 'knowing_server_id') or -1
racingServerId = getDbField(configCollection, "IDs", 'racing_server_id') or -1
serveringServerId = getDbField(configCollection, "IDs", 'servering_server_id') or -1
loggingChannelId = getDbField(configCollection, "IDs", 'logging_channel_id') or -1
hallChannelId = getDbField(configCollection, "IDs", 'hall_channel_id') or -1
screenedRoleId = getDbField(configCollection, "IDs", 'screened_role_id') or -1
vacanciesChannelId = getDbField(configCollection, "IDs", 'vacancies_channel_id') or -1
vacanciesMessageId = getDbField(configCollection, "IDs", 'vacancies_message_id') or -1

def getCrewNames():
    return getDbField(configCollection, "crews", "value") or []

class Member:
    def __init__(self, admin: bool, leader: bool, id: int, name: str, multiple: int):
        self.admin = admin
        self.leader = leader
        self.id = id
        self.name = name
        self.multiple = multiple

def sortFunction(member: Member):
    if member.leader:
        return '0 '+member.name
    if member.admin:
        return '1 '+member.name
    return "2 "+member.name

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
            number+=char
    return int(number)

def getScoreWithSeparator(intScore):
    scoreWithSeparator = ''
    while intScore > 0:
        number = str(intScore%1000)
        while len(number)<3:
            number = '0'+number
        scoreWithSeparator = '’'+number+scoreWithSeparator
        intScore//=1000
    while scoreWithSeparator[0]=='0' or scoreWithSeparator[0]=='’':
        scoreWithSeparator = scoreWithSeparator[1:]
    return scoreWithSeparator

async def makeTransfers(ctx: discord.ApplicationContext, season: int):
    currentSeason = getCurrentSeason()
    if ctx.guild is None:
        return "Something is terribly wrong. Contact server admins."
    transfers = movesCollection.find({"season": currentSeason-1})
    crewsToUpdateMembers = set()
    for transfer in transfers:
        try:
            player = await ctx.guild.fetch_member(transfer['player'])
        except:
            movesCollection.delete_many({"player": transfer['player']})
            continue
        crewFromRoleName = str(getDbField(crewCollection, transfer['crew_from'], 'member'))
        crewToRoleName = str(getDbField(crewCollection, transfer['crew_to'], 'member'))
        if checkRole(ctx, player, transfer['crew_from'])[0] == True:
            crewToRole = getRole(ctx, crewToRoleName)
            if crewToRole != None:
                await player.add_roles(crewToRole)
            crewFromRole = getRole(ctx, crewFromRoleName)
            if crewFromRole != None:
                await player.remove_roles(crewFromRole)
        multipleEntry = multipleAccountsCollection.find_one({"key": transfer['crew_from']})
        if multipleEntry is None and transfer['number_of_accounts'] > 1:
            continue
        if multipleEntry is not None:
            currentMultipleValue = multipleEntry[str(transfer['player'])]
            newMultipleValue = currentMultipleValue - transfer['number_of_accounts']
            if newMultipleValue != 1:
                multipleAccountsCollection.update_one({"key": transfer['crew_from']}, {"$set": {str(transfer['player']): newMultipleValue}})
            if transfer['number_of_accounts'] > 1:
                multipleAccountsCollection.find_one_and_update({"key": transfer['crew_to']}, {"$set": {str(transfer['player']): transfer['number_of_accounts']}})
        if crewToRoleName == "Out of family" and transfer['should_kick'] == True:
            await player.kick(reason="Kicked by Fawkes via transfer")
        movesCollection.delete_one(transfer)
        await deleteMovementFromMessage(ctx, transfer['crew_from'], "OUT")
        await deleteMovementFromMessage(ctx, transfer['crew_to'], "IN")
        crewsToUpdateMembers.add(transfer['crew_from'])
        crewsToUpdateMembers.add(transfer['crew_to'])
    for crew in crewsToUpdateMembers:
        if crew not in ['New to family', 'Out of family']:
            await getPlayersResponse(ctx, crew)


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

async def reorderChannels(ctx: discord.ApplicationContext, scores: dict, crewName: str):
    sortedScores = dict(sorted(scores.items(), key=lambda item: item[1],reverse=True))
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

async def getMessage(ctx, crewData, keyToGet, channelKey, initialMessage):
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

def getMembers(guild: discord.Guild, crewName, adminRoleName, leaderRoleName, memberRoleName, multipleAccountsIds, multipleAccountsData):
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
                for i in range(multipleAccountsData[memberId]-1):
                    newMemberStruct = Member(False, False, member.id, member.display_name, i+2)
                    response.append(newMemberStruct)
            else:
                multipleAccountsCollection.update_one({"key": crewName}, {"$unset": {memberId: ""}})
    return response

async def getPlayersResponse(ctx: discord.ApplicationContext, key: str):
    multipleAccountsData = multipleAccountsCollection.find_one({"key": key}, {"_id": 0})
    if multipleAccountsData != None:
        multipleAccountsIds = [key for key in multipleAccountsData if key != 'key']
    else:
        multipleAccountsIds = []
    crewData = crewCollection.find_one({"key": key}, {"_id": 0}) or {}
    crewName = getDbField(crewCollection, key, 'member') or ""
    message = await getMessage(ctx, crewData, "message_id", "members_channel_id", "**__Members for "+crewName.upper()+"__**")
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
        return "Role not found on the server! Try again and change the name to the exact name of the role you want info for!"
    response = getMembers(guild, crewName, adminRoleName, leaderRoleName, memberRoleName, multipleAccountsIds, multipleAccountsData)
    response.sort(key = sortFunction)
    await updateVacancies(ctx, key, response)

    stringResponse = '**__Members of '+crewName.upper()+"__**\n"
    number = 1
    for member in response:
        stringResponse+=str(number) + ". <@!"+str(member.id)+">"
        if member.multiple:
            stringResponse+=" "+str(member.multiple)
        if member.leader:
            stringResponse+=" -> **Leader**"
        elif member.admin:
            stringResponse+=" -> *Admin*"
        stringResponse+='\n'
        number+=1
    if message is not None:
        await message.edit(content = stringResponse)
    return "OK, all good."

async def updateVacancies(ctx: discord.ApplicationContext, crewName: str, membersList: list = []):
    currentSeason = getCurrentSeason()
    currentSeasonCount = len(membersList)
    vacanciesEntry = vacanciesCollection.find_one({}) or {}
    if currentSeasonCount == 0:
        if crewName in vacanciesEntry:
            currentSeasonCount = vacanciesEntry[crewName]['current']
        else:
            currentSeasonCount = 0
    nextSeasonCount = currentSeasonCount
    for move in list(movesCollection.find({"crew_to": crewName, "season": currentSeason+1})):
        nextSeasonCount += move['number_of_accounts']
    for move in list(movesCollection.find({"crew_from": crewName, "season": currentSeason+1})):
        nextSeasonCount -= move['number_of_accounts']
    vacanciesCollection.update_one({}, {"$set": {crewName: {"current": currentSeasonCount, "next": nextSeasonCount}}})
    messageContent ="**__Latest Crew Vacancies__**\n\n"
    for region in crewRegion.keys():
        messageContent += f"**__{region} Crews__**\n\n"
        for crewName in crewRegion[region]:
            if crewName not in vacanciesEntry.keys():
                continue
            messageContent += f"**{crewName.capitalize()}**\n{vacanciesEntry[crewName]['current']}/30 Current Season\n{vacanciesEntry[crewName]['next']}/30 Next Season\n"
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
    if crewData == None:
        return
    if inOrOut == "IN":
        messageIdKey = 'in_message_id'
        initialMessage = "Players Joining:"
    else:
        messageIdKey = 'out_message_id'
        initialMessage = "Players Leaving:"
    message = await getMessage(ctx, crewData, messageIdKey, 'members_channel_id', initialMessage)
    await updateMovementsMessage(ctx, message, crewName, inOrOut)

async def kickOrBanOrUnban(user: discord.Member, op: str, bot: discord.Bot, reason=None):
    for guild in bot.guilds:
        if guild.id in [racingServerId, serveringServerId, risingServerId, knowingServerId]:
            print("Doing "+op+" for user: "+user.name+" in the server named: "+guild.name)
            if op=='kick':
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
        multipleAccountsCollection.find_one_and_update({"key": crewName}, {"$set": {memberId: numberOfAccounts}}, upsert=True)
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
    return int((time.time()-(getDbField(configCollection, 'time', 'value') or 0))/60/60/24/7/2)+166

async def processTransfer(ctx: discord.ApplicationContext, player: discord.Member, crewFrom: str, crewTo: str, numberOfAccounts: int, season: int, pingAdmin: bool, shouldKick: bool):
    if crewFrom == "New to family" and crewTo == "Out of family":
        return "A player can't be new to family and going out of family at the same time"
    if crewFrom == crewTo:
        return "A move can't take place within the same crew."
    if crewTo == "Out of family" and shouldKick == None:
        return "Set should_kick for this kind of move."
    if season<getCurrentSeason()+int(crewFrom!="New to family"):
        return "Transfers can only happen in the future, for members who were left out by mistake simply add the role and run /members command. The only transfers that can happen in the current season are the new players."
    message = await processMovement(ctx, crewFrom, crewTo, player, numberOfAccounts, season, pingAdmin, shouldKick)
    return message

def checkRole(ctx: discord.ApplicationContext, player: discord.Member, crewName: str):
    movesData = list(movesCollection.find({"player": player.id})).sort(key=lambda elem: elem['season'])
    crewData = crewCollection.find_one({"key": crewName}, {"_id": 0, "member": 1})
    if movesData is not None:
        lastMove = movesData[-1]
        if lastMove['crew_to'] != crewName:
            return (False, f"I looked at this player history of movements and from what I can see, he will NOT be in **{getDbField(crewCollection, crewName, 'member')}** at the time of the transfer. Last move is registered to {lastMove['crew_to']} in season {lastMove['season']}. If your move is before that you'll have to redo the path till then so we don't risk mising links between seasons. Talk with <@308561593858392065> about how to do this.")
        return (True, "history")
    if crewData == None:
        role = getRole(ctx, "Temporary Visitor Pass")
        if role is None or player.get_role(role.id) is None:
            return (True, False)
        return (True, True)
    roleName = crewData['member']
    role = getRole(ctx, roleName)
    if role is None or player.get_role(role.id) == None:
        return (False, "The player does not have the crew role. Add the role and try again.")
    return (True, "crew_role")

def checkForNumberOfAccounts(player: discord.Member, crewName: str, numberOfAccountsToMoveNext: int):
    crewData = crewCollection.find_one({"key": crewName})
    if crewData is None:
        return True
    multipleData = multipleAccountsCollection.find_one({"key": crewName}, {"_id": 0, str(player.id): 1})
    if multipleData == None or str(player.id) not in multipleData.keys():
        numberOfAccountsAvailableToMove = 1
    else:
        numberOfAccountsAvailableToMove = multipleData[str(player.id)]
    existingMovesData = movesCollection.find({"player": player.id, "crew_from": crewName})
    for existingMove in existingMovesData:
        numAccounts = existingMove['number_of_accounts'] if 'number_of_accounts' in existingMove.keys() else 1
        numberOfAccountsAvailableToMove-=numAccounts
    return numberOfAccountsAvailableToMove>=numberOfAccountsToMoveNext

async def processMovement(ctx: discord.ApplicationContext, crewFrom: str, crewTo: str, player: discord.Member, numberOfAccounts: int, season: int, pingAdmin: bool, shouldKick: bool) -> str:
    movementData = movesCollection.find_one({"player": player.id, "crew_from": crewFrom, "crew_to": crewTo})
    if numberOfAccounts is None:
        numberOfAccounts = 1
    if movementData is not None:
        print(f"Existing move found: {movementData['player']} from {crewFrom} to {crewTo} with {movementData['number_of_accounts']} accounts. Deleting that to update the entry.")
        movesCollection.delete_one({"player": player.id, "crew_from": crewFrom, "crew_to": crewTo})
    roleCheck = checkRole(ctx, player, crewFrom)
    if roleCheck[0] == False:
        return roleCheck[1]
    shouldSendMessageInHall = roleCheck[1] == True and (crewFrom == "New to family")
    if checkForNumberOfAccounts(player, crewFrom, numberOfAccounts) == False:
        return "The player has too many accounts registered to transfer with this transfer included. Check the multiple or remove from the existing transfers for this player first."
    objectToInsert = {"player": player.id, "crew_from": crewFrom, "crew_to": crewTo, "number_of_accounts": numberOfAccounts, "season": season}
    if shouldKick != None and crewTo == "Out of family":
        objectToInsert["should_kick"]=True
    movesCollection.insert_one(objectToInsert)
    crewFromData = crewCollection.find_one({"key": crewFrom}, {"_id": 0})
    if crewFromData is not None:
        outMessage = await getMessage(ctx, crewFromData, 'out_message_id', "members_channel_id", "**OUT:**")
        await updateMovementsMessage(ctx, outMessage, crewFrom, 'OUT')
    crewToData = crewCollection.find_one({"key": crewTo}, {"_id": 0})
    if crewToData is not None:
        inMessage = await getMessage(ctx, crewToData, "in_message_id", "members_channel_id", "**IN:**")
        await updateMovementsMessage(ctx, inMessage, crewTo, "IN")
    await sendMessageInTheHallAndAddScreened(ctx, player, "!"+crewTo, shouldSendMessageInHall)
    await updateVacancies(ctx, crewFrom)
    await updateVacancies(ctx, crewTo)
    await sendMessageToAdminChat(ctx, crewTo, player, "confirm", "to", pingAdmin, season, numberOfAccounts)
    await sendMessageToAdminChat(ctx, crewFrom, player, "confirm", "from", pingAdmin, season, numberOfAccounts)
    return "Transfer processed successfully"

async def sendMessageToAdminChat(ctx: discord.ApplicationContext, crew: str, player: discord.Member, confirmOrCancel: str, toOrFrom: str, pingAdmin: bool, season: int, numberOfAccounts: int):
    if pingAdmin == False:
        return
    crewData = crewCollection.find_one({"key": crew}, {"admin_channel_id": 1, "admin": 1, "_id": 0})
    if crewData is None:
        return
    adminRole = getRole(ctx, crewData['admin'])
    if adminRole is None:
        return
    message = ""
    if confirmOrCancel == "confirm" and ctx.author:
        message = f"{adminRole.mention},\n{ctx.author.mention} confirmed that {player.mention} will be moving {toOrFrom} your crew in S{season} with {numberOfAccounts} account" + "s." if numberOfAccounts>1 else "."
    elif ctx.author:
        message = f"{adminRole.mention},\n{ctx.author.mention} has just canceled a scheduled move of {player.mention} {toOrFrom} your crew in S{season} with {numberOfAccounts} account" + "s." if numberOfAccounts>1 else "."
    channel = await ctx.bot.fetch_channel(crewData['admin_channel_id'])
    if isinstance(channel, discord.TextChannel):
        await channel.send(message)

async def sendMessageInTheHallAndAddScreened(ctx: discord.ApplicationContext, member: discord.Member, password: str, shouldSend: bool):
    guild = ctx.guild
    if shouldSend == False or guild is None:
        return
    channel = await ctx.bot.fetch_channel(hallChannelId)
    role = guild.get_role(screenedRoleId)
    if role is None:
        return
    await member.add_roles(role)
    if isinstance(channel, discord.TextChannel):
        await channel.send(f"""
Hi, {member.mention}, in addition to the rules you already accepted when joining the server (**i.e, no cheats or modded accounts allowed, no drama, 16+ minimum age**) these are the general rules of all our crews:
    

**1. Please Complete All Cups**
…any that give RP and/or Wildcard tokens, and Weekly Elite Cup races.

**2. Please Follow Wildcard Schedule**
Donate ONLY if the day's card is not filled. ACTIVATING WILDCARD = INSTANT REMOVAL!

**3. Communication ESSENTIAL!**
We don't ask for you to be a chatterbox unless you want to. But if you suddenly struggle for time and need some help, please ASK in your crew chat. It is not fair on a crew's top players if you are at the bottom, unreachable and struggling to beat the minimum, and you may be removed.

**4. Keep Your Server Nickname Same As Your In-Game-Name**
Helps to ensure we don't accidentally boot you from the server! 😅

*If you aren't clear on any of the rules and wish a more detailed breakdown, please send the following command here as a message:*

!ruless

*If you are happy with your understanding of the crew rules, to open the server and be able to meet your new crew-mates and family members please send the following message in this channel containing exactly the following:*

{password}
""")

async def updateMovementsMessage(ctx: discord.ApplicationContext, message, crewName, inOrOut):
    newMessage = f"**Players {'Joining' if inOrOut=='IN' else 'Leaving'}:**\n\n"
    movementsKey = "crew_from" if inOrOut=="OUT" else "crew_to"
    crewKey = "crew_to" if inOrOut=="OUT" else "crew_from"
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
        except:
            movesCollection.delete_many({"player": move['player']})
            continue
        if member is not None:
            newMessage+=f"{str(idx)}. {member.mention} "    
        if crewData is None:
            newMessage += f"{move[crewKey]} in S{str(move['season'])}"
        else:
            crewRole = getRole(ctx, crewData['member'])
            numberOfAccounts = move['number_of_accounts']
            newMessage += f'{"from" if inOrOut == "IN" else "to"} {crewRole.mention if crewRole is not None else ""}{f" with {numberOfAccounts} accounts" if numberOfAccounts>1 else ""} in S{str(move["season"])}'
        newMessage += '\n'
        idx+=1
    await message.edit(newMessage)

async def unregisterTransfer(ctx: discord.ApplicationContext, player: discord.Member, crewFrom, crewTo, pingAdmin = True):
    if crewTo != crewFrom and (crewTo == None or crewFrom == None):
        return "if you give one of crew_from and crew_to, you must give the other as well."
    if crewTo == crewFrom and crewTo != None:
        return "A movement can't be within the same crew, so I also can't unregister this kind of moves."
    print(f"Unregister transfer of {player.display_name} from {crewFrom} to {crewTo}")
    if crewTo == None:
        moves = list(movesCollection.find({"player": player.id}))
        if len(moves)==0:
            return "No moves found for this player."
        if len(moves)>1:
            return "Too many moves found, add crew_from and crew_to and try again."
        move = moves[0]
        result = movesCollection.delete_many({"player": move['player']})
        await deleteMovementFromMessage(ctx, move['crew_from'], "OUT")
        await deleteMovementFromMessage(ctx, move['crew_to'], "IN")
        await updateVacancies(ctx, move['crew_from'])
        await updateVacancies(ctx, move['crew_to'])
        await sendMessageToAdminChat(ctx, move['crew_to'], player, "cancel", "to", pingAdmin, move['season'], move['number_of_accounts'])
        await sendMessageToAdminChat(ctx, move['crew_from'], player, "cancel", "from", pingAdmin, move['season'], move['number_of_accounts'])
        return f"Transfer/s cancelled. {result.deleted_count} moves for {player.name}#{player.discriminator}"
    move = list(movesCollection.find({"player": player.id, "crew_from": crewFrom, "crew_to": crewTo}))[0]
    movesCollection.delete_one({"player": move['player']})
    await deleteMovementFromMessage(ctx, move['crew_from'], "OUT")
    await deleteMovementFromMessage(ctx, move['crew_to'], "IN")
    await updateVacancies(ctx, move['crew_from'])
    await updateVacancies(ctx, move['crew_to'])
    await sendMessageToAdminChat(ctx, move['crew_to'], player, "cancel", "to", pingAdmin, move['season'], move['number_of_accounts'])
    await sendMessageToAdminChat(ctx, move['crew_from'], player, "cancel", "from", pingAdmin, move['season'], move['number_of_accounts'])
    return f"Cancelled transfer for {player.name}#{player.discriminator} from {crewFrom} to {crewTo}"
