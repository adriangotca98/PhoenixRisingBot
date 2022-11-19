from typing import List
import discord
from pymongo import MongoClient
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

scores = {}
crewRegion = configCollection.find_one({"key": "crew_region"}, {"_id": 0, "value": 1})['value']
discord_bot_token = configCollection.find_one({"key": "discord_token"}, {"_id": 0, "value": 1})['value']
IDs = configCollection.find_one({"key": "IDs"}, {"_id": 0})
risingServerId = IDs['rising_server_id']
knowingServerId = IDs['knowing_server_id']
racingServerId = IDs['racing_server_id']
serveringServerId = IDs['servering_server_id']
loggingChannelId = IDs['logging_channel_id']
hallChannelId = IDs['hall_channel_id']
screenedRoleId = IDs['screened_role_id']
vacanciesChannelId = IDs['vacancies_channel_id']
if 'vacancies_message_id' in IDs.keys():
    vacanciesMessageId = IDs['vacancies_message_id']
else:
    vacanciesMessageId = None

def getCrewNames():
    return configCollection.find_one({"key": "crews"}, {"_id": 0, "value": 1})['value']

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
    for crew in getCrewNames():
        channelId = crewCollection.find_one({'key': crew},{"_id": 0, "leaderboard_id": 1})['leaderboard_id']
        channel = await bot.fetch_channel(channelId)
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

async def setScore(ctx: discord.ApplicationContext, crewName: str, score: str):
    print(f"Setting score {str(score)} for {crewName}")
    channelId = crewCollection.find_one({'key': crewName},{"_id": 0, "leaderboard_id": 1})['leaderboard_id']
    channel: discord.channel.CategoryChannel = await ctx.bot.fetch_channel(channelId)
    channelName = channel.name
    newChannelName = channelName.strip("0123456789'`’") + getScoreWithSeparator(int(score))
    await channel.edit(name=newChannelName)
    scores[crewName] = int(score)
    await reorderChannels(ctx, scores, crewName)

async def reorderChannels(ctx: discord.ApplicationContext, scores: dict, crewName: str):
    sortedScores = dict(sorted(scores.items(), key=lambda item: item[1],reverse=True))
    channelId = crewCollection.find_one({'key': crewName},{"_id": 0, "leaderboard_id": 1})['leaderboard_id']
    channel: discord.abc.GuildChannel = await ctx.bot.fetch_channel(channelId)
    if list(sortedScores.keys())[0] == crewName:
        await channel.move(beginning=True)
        return
    for key in sortedScores:
        if key == crewName:
            aboveChannelId: int = crewCollection.find_one({'key': lastKey},{"_id": 0, "leaderboard_id": 1})['leaderboard_id']
            aboveChannel: discord.abc.GuildChannel = await ctx.bot.fetch_channel(aboveChannelId)
            await channel.move(after=aboveChannel)
            return
        lastKey = key

async def updateMessage(ctx: discord.ApplicationContext, crewData, keyToSet, initialMessage):
    key = crewData['key']
    channelId = crewData['members_channel_id']
    channel = await ctx.bot.fetch_channel(channelId)
    message = await channel.send(initialMessage)
    crewCollection.update_one({"key": key}, {"$set": {keyToSet: message.id}})
    return message

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

async def deleteNewcomers(ctx: discord.ApplicationContext, members: list[Member], crewName: str, shouldDeleteNewcomers: bool):
    currentSeason = getCurrentSeason()
    for i in range(len(members)):
        if i>=len(members):
            break
        member = members[i]
        movement = movesCollection.find_one({"player": member.id, "crew_from": "New to family", "crew_to": crewName, "season": currentSeason}, {"_id": 0})
        crewData = crewCollection.find_one({"key": crewName})
        message = await getMessage(ctx, crewData, "in_message_id", "members_channel_id", "**Players Joining:**")
        if movement is not None:
            if shouldDeleteNewcomers:
                movesCollection.delete_one({{"player": member.id, "crew_from": "New to family", "crew_to": crewName, "season": currentSeason}})
                await updateMovementsMessage(ctx, message, crewName, "IN")
            else:
                members.pop(i)
                i-=1
    return members

async def getPlayersResponse(ctx: discord.ApplicationContext, key: str, shouldDeleteFreshMovements):
    multipleAccountsData = multipleAccountsCollection.find_one({"key": key}, {"_id": 0})
    if multipleAccountsData != None:
        multipleAccountsIds = [key for key in multipleAccountsData if key != 'key']
    else:
        multipleAccountsIds = []
    crewData = crewCollection.find_one({"key": key}, {"_id": 0})
    crewName = crewData['member']
    message = await getMessage(ctx, crewData, "message_id", "members_channel_id", "**__Members for "+crewName.upper()+"__**")
    memberRoleName = crewData['member']
    adminRoleName = crewData['admin']
    leaderRoleName = crewData['leader']
    guild: discord.Guild = ctx.guild
    roleFound = False
    for role in guild.roles:
        if role.name == memberRoleName:
            roleFound = True
    if not roleFound:
        return "Role not found on the server! Try again and change the name to the exact name of the role you want info for!"
    response = getMembers(guild, crewName, adminRoleName, leaderRoleName, memberRoleName, multipleAccountsIds, multipleAccountsData)
    response.sort(key = sortFunction)
    status = await checkMovements(ctx, response, crewData, shouldDeleteFreshMovements)
    response = await deleteNewcomers(ctx, response, key, shouldDeleteFreshMovements)
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
    await message.edit(content = stringResponse)
    return status

async def updateVacancies(ctx: discord.ApplicationContext, crewName: str, membersList: list = []):
    currentSeason = getCurrentSeason()
    currentSeasonCount = len(membersList)
    if currentSeasonCount == 0:
        if crewName in vacanciesCollection.find_one({}):
            currentSeasonCount = vacanciesCollection.find_one({})[crewName]['current']
        else:
            currentSeasonCount = 0
    nextSeasonCount = currentSeasonCount
    for move in list(movesCollection.find({"crew_to": crewName, "season": currentSeason+1})):
        nextSeasonCount += move['number_of_accounts']
    for move in list(movesCollection.find({"crew_from": crewName, "season": currentSeason+1})):
        nextSeasonCount -= move['number_of_accounts']
    vacanciesCollection.update_one({}, {"$set": {crewName: {"current": currentSeasonCount, "next": nextSeasonCount}}})
    vacanciesEntry = vacanciesCollection.find_one({}, {"_id": 0})
    messageContent ="**__Latest Crew Vacancies__**\n\n"
    for region in crewRegion.keys():
        messageContent += f"**__{region} Crews__**\n\n"
        for crewName in crewRegion[region]:
            if crewName not in vacanciesEntry.keys():
                continue
            messageContent += f"**{crewName.capitalize()}**\n{vacanciesEntry[crewName]['current']}/30 Current Season\n{vacanciesEntry[crewName]['next']}/30 Next Season\n"
        messageContent += "\n"
    channel = await ctx.guild.fetch_channel(vacanciesChannelId)
    try:
        if vacanciesMessageId is not None:
            message = await channel.fetch_message(vacanciesMessageId)
            await message.edit(content=messageContent)
        else:
            message = await channel.send(messageContent)
            configCollection.update_one({"key": "IDs"}, {"$set": {"vacancies_message_id": message.id}})    
    except discord.errors.NotFound:
        message = await channel.send(messageContent)
        configCollection.update_one({"key": "IDs"}, {"$set": {"vacancies_message_id": message.id}})

async def checkMovements(ctx: discord.ApplicationContext, response: List[Member], crewData: dict, shouldDeleteFreshMovements):
    currentSeason = getCurrentSeason()
    outOfFamilyMoves = list(movesCollection.find({"crew_from": crewData['key'], "crew_to": "Out of family", "season": currentSeason}))
    for move in outOfFamilyMoves:
        member = await ctx.guild.fetch_member(move['player'])
        roleFound = False
        for role in member.roles:
            roleFound = roleFound or (role.name == crewData['member'])
        if roleFound == False:
            movesCollection.delete_one({"crew_from": crewData['key'], "crew_to": "Out of family", "player": move['player'], "season": currentSeason})
            await deleteMovementFromMessage(ctx, crewData['key'], "OUT")
    for member in response:
        movesData = list(movesCollection.find({"player": member.id, "crew_to": crewData['key'], "season": currentSeason}))
        memberId = str(member.id)
        for move in movesData:
            crewFrom = move['crew_from']
            crewTo = move['crew_to']
            if crewFrom == 'New to family' and not shouldDeleteFreshMovements:
                continue
            oldMultiple = multipleAccountsCollection.find_one({"key": crewFrom}, {memberId: 1})
            if oldMultiple is not None and memberId in oldMultiple.keys():
                newMultiple = oldMultiple[memberId] - move['number_of_accounts']
                if newMultiple > 1:
                    multipleAccountsCollection.update_one({"key": crewFrom}, {"$set": {memberId: newMultiple}})
                else:
                    multipleAccountsCollection.update_one({"key": crewFrom}, {"$unset": {memberId: ""}})
                if move['number_of_accounts'] != 1:
                    multipleAccountsCollection.update_one({"key": crewTo}, {"$set": {memberId: move['number_of_accounts']}})
            movesCollection.delete_one({"season": currentSeason, "player": move['player'], "crew_from": move['crew_from'], "crew_to": move['crew_to']})
            await deleteMovementFromMessage(ctx, crewFrom, "OUT")
            await deleteMovementFromMessage(ctx, crewTo, "IN")
    if vacanciesCollection.find({"season": {"$lt": currentSeason}, "crew_from": crewData['key']}) != [] or vacanciesCollection.find({"season": {"$lt": currentSeason}, "crew_to": crewData['key']}) != []:
       return "Old moves are still in the list. Check which are in the `Players Joining:` and `Players Leaving:` and either unregister them or make them."
    return "OK, all good!"

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
    memberRoleName = crewCollection.find_one({"key": crewName}, {"_id": 0, "member": 1})['member']
    roles = user.roles
    roleFound = False
    for role in roles:
        if role.name == memberRoleName:
            roleFound = True
            break
    if not roleFound:
        return "User does not have crew role! Add crew role and try again."
    memberId = str(user.id)
    existingEntry = multipleAccountsCollection.find_one({"key": crewName},{"_id": 0, memberId: 1})
    if existingEntry == None:
        if numberOfAccounts != 1:
            multipleAccountsCollection.insert_one({"key": crewName, memberId: numberOfAccounts})
    else:
        if numberOfAccounts != 1:
            multipleAccountsCollection.update_one({"key": crewName}, {"$set": {memberId: numberOfAccounts}})
        else:
            multipleAccountsCollection.update_one({"key": crewName}, {"$unset": {memberId: ""}})
    return "Multiple accounts recorded!"

def getRole(ctx: discord.ApplicationContext, roleName: str):
    for role in ctx.guild.roles:
        if role.name == roleName:
            return role
    return None

def getCurrentSeason():
    return int((time.time()-configCollection.find_one({"key": "time"}, {"_id": 0})['value'])/60/60/24/7/2)+166

async def processTransfer(ctx: discord.ApplicationContext, player: discord.Member, crewFrom: str, crewTo: str, numberOfAccounts: int, season: int):
    if crewFrom == "New to family" and crewTo == "Out of family":
        return "A player can't be new to family and going out of family at the same time"
    if crewFrom == crewTo:
        return "A move can't take place within the same crew."
    roleCheck = checkRole(ctx, player, crewFrom)
    if season<getCurrentSeason()+int(crewFrom!="New to family"):
        return "Transfers can only happen in the future, for members who were left out by mistake simply add the role and run /members command. The only transfers that can happen in the current season are the new players."
    message = await processMovement(ctx, crewFrom, crewTo, player, numberOfAccounts, season)
    return message

def checkRole(ctx: discord.ApplicationContext, player: discord.Member, crewName: str):
    movesData = list(movesCollection.find({"player": player.id})).sort(key=lambda elem: elem['season'])
    crewData = crewCollection.find_one({"key": crewName}, {"_id": 0, "member": 1})
    if movesData is not None:
        lastMove = movesData[-1]
        if lastMove['crew_to'] != crewName:
            return {False, f"I looked at this player history of movements and from what I can see, he will NOT be in **{crewData['member']}** at the time of the transfer. Last move is registered to {lastMove['crew_to']} in season {lastMove['season']}. If your move is before that you'll have to redo the path till then so we don't risk mising links between seasons. Talk with <@308561593858392065> about how to do this."}
        return (True, "history")
    if crewData == None:
        role = getRole(ctx, "Temporary Visitor Pass")
        if player.get_role(role.id) == None:
            return (True, False)
        return (True, True)
    roleName = crewData['member']
    role = getRole(ctx, roleName)
    if player.get_role(role.id) == None:
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

async def processMovement(ctx: discord.ApplicationContext, crewFrom: str, crewTo: str, player: discord.Member, numberOfAccounts: int, season: int) -> str:
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
    movesCollection.insert_one({"player": player.id, "crew_from": crewFrom, "crew_to": crewTo, "number_of_accounts": numberOfAccounts, "season": season})
    crewFromData = crewCollection.find_one({"key": crewFrom}, {"_id": 0})
    if crewFromData is not None:
        outMessage = await getMessage(ctx, crewFromData, 'out_message_id', "members_channel_id", "**OUT:**")
        await updateMovementsMessage(ctx, outMessage, crewFrom, 'OUT')
    crewToData = crewCollection.find_one({"key": crewTo}, {"_id": 0})
    if crewToData is not None:
        inMessage = await getMessage(ctx, crewToData, "in_message_id", "members_channel_id", "**IN:**")
        await updateMovementsMessage(ctx, inMessage, crewTo, "IN")
    if crewFrom == "New to family":
        await sendMessageInTheHallAndAddScreened(ctx, player, "!"+crewTo, shouldSendMessageInHall)
    await updateVacancies(ctx, crewFrom)
    await updateVacancies(ctx, crewTo)
    return "Transfer processed successfully"

async def sendMessageInTheHallAndAddScreened(ctx: discord.ApplicationContext, member: discord.Member, password: str, shouldSend: bool):
    if shouldSend == False:
        return
    channel = await ctx.guild.fetch_channel(hallChannelId)
    role = ctx.guild.get_role(screenedRoleId)
    await member.add_roles(role)
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
    for move in movements:
        crewData = crewCollection.find_one({"key": move[crewKey]}, {"_id": 0})
        member = await ctx.guild.fetch_member(move['player'])
        newMessage+=f"{member.mention} "    
        if crewData is None:
            newMessage += move[crewKey] + " in S" + str(move['season'])
        else:
            crewRole = getRole(ctx, crewData['member'])
            newMessage += "from" if inOrOut == "IN" else "to"
            newMessage += " " + crewRole.mention
            newMessage += " in S" + str(move['season'])
        newMessage += '\n'
    await message.edit(newMessage)

async def unregisterTransfer(ctx: discord.ApplicationContext, player: discord.Member, crewFrom, crewTo):
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
        return f"Transfer/s cancelled. {result.deleted_count} moves for {player.name}#{player.discriminator}"
    move = list(movesCollection.find({"player": player.id, "crew_from": crewFrom, "crew_to": crewTo}))[0]
    movesCollection.delete_one({"player": move['player']})
    await deleteMovementFromMessage(ctx, move['crew_from'], "OUT")
    await deleteMovementFromMessage(ctx, move['crew_to'], "IN")
    await updateVacancies(ctx, move['crew_from'])
    await updateVacancies(ctx, move['crew_to'])
    return f"Cancelled transfer for {player.name}#{player.discriminator} from {crewFrom} to {crewTo}"
