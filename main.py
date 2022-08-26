import discord
from discord.ext import commands
import json
import os
import re

f = open("./constants.json")
rolesPerCrewAndColor = json.load(f)
serveringServerId = os.environ.get("SERVERING_SERVER_ID")
risingServerId = os.environ.get("RISING_SERVER_ID")
knowingServerId = os.environ.get("KNOWING_SERVER_ID")
racingServerId = os.environ.get("RACING_SERVER_ID")


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

async def sendInitMessage(ctx, crewNameCaps, crewName):
    message = await ctx.send("**__Members for "+crewNameCaps+"__**")
    rolesPerCrewAndColor[crewName]['messageId'] = message.id

async def kickOrBanOrUnban(ctx, user: str, op: str, bot: commands.Bot, **kwargs):
    userId = int(re.findall(r'\d+', user)[0])
    for guild in bot.guilds:
        if guild.id in [racingServerId, serveringServerId, risingServerId, knowingServerId]:
            if op=='kick':
                await guild.kick(bot.fetch_user(userId), reason=kwargs['reason'])
            elif op == 'ban':
                await guild.ban(bot.fetch_user(userId))
            elif op == 'unban':
                await guild.unban(bot.fetch_user(userId), reason=kwargs['reason'])