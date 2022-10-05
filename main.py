import discord
import json
import re
from pymongo import MongoClient

client = MongoClient("mongodb+srv://<username>:<password>@phoenixrisingcluster.p2zno6x.mongodb.net/?retryWrites=true&w=majority")
crewDataCollection = client.get_database("Fawkes").get_collection("crewData")
configCollection = client.get_database("Fawkes").get_collection("configData")

scores = {}
crewNames = configCollection.find_one({"key": "crews"}, {"_id": 0, "value": 1})['value']
serveringServerId = configCollection.find_one({"key": "servers"}, {"_id": 0, "servering": 1})['servering']
risingServerId = configCollection.find_one({"key": "servers"}, {"_id": 0, "rising": 1})['rising']
knowingServerId = configCollection.find_one({"key": "servers"}, {"_id": 0, "knowing": 1})['knowing']
racingServerId = configCollection.find_one({"key": "servers"}, {"_id": 0, "racing": 1})['racing']
discord_bot_token = configCollection.find_one({"key": "discord_token"}, {"_id": 0, "value": 1})['value']


class Member:
    def __init__(self, admin: bool, leader: bool, id: int, name: str):
        self.admin = admin
        self.leader = leader
        self.id = id
        self.name = name

def sortFunction(member: Member):
    if member.leader:
        return '0 '+member.name
    if member.admin:
        return '1 '+member.name
    return "2 "+member.name

async def init(bot: discord.Bot):
    for crew in crewNames:
        channelId = crewDataCollection.find_one({'key': crew},{"_id": 0, "leaderboard_id": 1})['leaderboard_id']
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
    print(crewName)
    print(crewDataCollection.find_one({'key': crewName},{"_id": 0, "leaderboard_id": 1}))
    channelId = crewDataCollection.find_one({'key': crewName},{"_id": 0, "leaderboard_id": 1})['leaderboard_id']
    channel: discord.channel.CategoryChannel = await ctx.bot.fetch_channel(channelId)
    channelName = channel.name
    newChannelName = channelName.strip("0123456789'`’") + getScoreWithSeparator(int(score))
    await channel.edit(name=newChannelName)
    scores[crewName] = int(score)
    await reorderChannels(ctx, scores, crewName)

async def reorderChannels(ctx: discord.ApplicationContext, scores: dict, crewName: str):
    sortedScores = dict(sorted(scores.items(), key=lambda item: item[1],reverse=True))
    channelId = crewDataCollection.find_one({'key': crewName},{"_id": 0, "leaderboard_id": 1})['leaderboard_id']
    channel: discord.abc.GuildChannel = await ctx.bot.fetch_channel(channelId)
    if list(sortedScores.keys())[0] == crewName:
        await channel.move(beginning=True)
        return
    for key in sortedScores:
        if key == crewName:
            aboveChannelId: int = crewDataCollection.find_one({'key': lastKey},{"_id": 0, "leaderboard_id": 1})['leaderboard_id']
            aboveChannel: discord.abc.GuildChannel = await ctx.bot.fetch_channel(aboveChannelId)
            await channel.move(after=aboveChannel)
            return
        lastKey = key

async def updateMessage(ctx: discord.ApplicationContext, crewData):
    key = crewData['key']
    crewName = crewData['member']
    message = await ctx.send("**__Members for "+crewName.upper()+"__**")
    crewDataCollection.update_one({"key": key}, {"$set": {"message_id": message.id}})
    return message

async def getPlayersResponse(ctx: discord.ApplicationContext, key: str):
    crewData = crewDataCollection.find_one({"key": key}, {"_id": 0, "member": 1, "admin": 1, "key": 1, "leader": 1, "message_id": 1})
    crewName = crewData['member']
    if 'message_id' not in crewData.keys():
        message = await updateMessage(ctx, crewData)
    else:
        try:
            message = await ctx.fetch_message(crewData['message_id'])
        except discord.errors.NotFound:
            print('Message not found. Creating another one :)')
            message = await updateMessage(ctx, crewName, key)
    memberRoleName = crewData['member']
    adminRoleName = crewData['admin']
    leaderRoleName = crewData['leader']
    guild: discord.Guild = ctx.guild
    roleFound = False
    for role in guild.roles:
        if role.name == memberRoleName:
            roleFound = True
    if not roleFound:
        await ctx.send_response("Role not found on the server! Try again and change the name to the exact name of the role you want info for!")
        return
    response = []
    for member in guild.members:
        roleNames = set([role.name for role in member.roles])
        memberStruct = Member(False, False, member.id, member.display_name)
        if adminRoleName in roleNames:
            memberStruct.admin = True
        if leaderRoleName in roleNames:
            memberStruct.leader = True
        if memberRoleName in roleNames:
            response.append(memberStruct)
    response.sort(key = sortFunction)

    stringResponse = '**__Members of '+crewName.upper()+"__**\n"
    number = 1
    for member in response:
        stringResponse+=str(number) + ". <@!"+str(member.id)+">"
        if member.leader:
            stringResponse+=" -> **Leader**"
        elif member.admin:
            stringResponse+=" -> *Admin*"
        stringResponse+='\n'
        number+=1
    await message.edit(content = stringResponse)

async def kickOrBanOrUnban(user: str, op: str, bot: discord.Bot, reason=None):
    userId = int(re.findall(r'\d+', user)[0])
    userObj = await bot.fetch_user(userId)
    for guild in bot.guilds:
        if guild.id in [racingServerId, serveringServerId, risingServerId, knowingServerId]:
            print("Doing "+op+" for user: "+userObj.name+" in the server named: "+guild.name)
            if op=='kick':
                await guild.kick(userObj, reason=reason)
            elif op == 'ban':
                await guild.ban(userObj, reason=reason, delete_message_days=0)
            elif op == 'unban':
                await guild.unban(userObj, reason=reason)