import discord
from discord.ext import commands
import json
import os
import re

f = open("./constants.json")
constants = json.load(f)
scores = {}
f.close()
serveringServerId = constants['servers']['servering']
risingServerId = constants['servers']['rising']
knowingServerId = constants['servers']['knowing']
racingServerId = constants['servers']['racing']


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

async def init(bot: commands.Bot):
    for crew in constants:
        if 'leaderboard_id' in constants[crew]:
            channelId = constants[crew]['leaderboard_id']
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
    

async def setScore(ctx: commands.Context, crewName: str, score: str):
    crewName = crewName.capitalize()
    channel: discord.channel.CategoryChannel = await ctx.bot.fetch_channel(constants[crewName]['leaderboard_id'])
    channelName = channel.name
    newChannelName = channelName.strip("0123456789'`’") + getScoreWithSeparator(int(score))
    await channel.edit(name=newChannelName)
    scores[crewName] = int(score)
    await reorderChannels(ctx, scores, crewName)

async def reorderChannels(ctx: commands.Context, scores: dict, crewName: str):
    sortedScores = dict(sorted(scores.items(), key=lambda item: item[1],reverse=True))
    if list(sortedScores.keys())[0] == crewName:
        channel: discord.abc.GuildChannel = await ctx.bot.fetch_channel(constants[crewName]['leaderboard_id'])
        await channel.move(beginning=True)
        return
    for key in sortedScores:
        if key == crewName:
            channel: discord.abc.GuildChannel = await ctx.bot.fetch_channel(constants[key]['leaderboard_id'])
            channelAbove: discord.abc.GuildChannel = await ctx.bot.fetch_channel(constants[lastKey]['leaderboard_id'])
            await channel.move(after=channelAbove)
            return
        lastKey = key

async def getPlayersResponse(ctx, rolesAndColor, crewName: str):
    memberRoleName = rolesAndColor['member']
    adminRoleName = rolesAndColor['admin']
    leaderRoleName = rolesAndColor['leader']
    guild: discord.Guild = ctx.guild
    roleFound = False
    for role in guild.roles:
        if role.name == memberRoleName:
            roleFound = True
    if not roleFound:
        await ctx.send("Role not found on the server! Try again and change the name to the exact name of the role you want info for!")
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
    
    message = await ctx.fetch_message(rolesAndColor['messageId'])
    await message.edit(content = stringResponse)

async def sendInitMessage(ctx: commands.Context, crewNameCaps, crewName):
    message = await ctx.send("**__Members for "+crewNameCaps+"__**")
    if 'messageId' in constants[crewName].keys():
        messageToDelete = await ctx.fetch_message(constants[crewName]['messageId'])
        await messageToDelete.delete()
    constants[crewName]['messageId'] = message.id
    file = open('./constants.json','w')
    json.dump(constants,file,indent=4)
    file.close()

async def kickOrBanOrUnban(user: str, op: str, bot: commands.Bot, **kwargs):
    userId = int(re.findall(r'\d+', user)[0])
    userObj = await bot.fetch_user(userId)
    for guild in bot.guilds:
        if guild.id in [racingServerId, serveringServerId, risingServerId, knowingServerId]:
            print("Doing "+op+" for user: "+userObj.name+" in the server named: "+guild.name)
            if op=='kick':
                await guild.kick(userObj, reason=kwargs['reason'])
            elif op == 'ban':
                await guild.ban(userObj)
            elif op == 'unban':
                await guild.unban(userObj, reason=kwargs['reason'])