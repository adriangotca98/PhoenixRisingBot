import discord
from discord.ext import commands
import json
import os
import re

f = open("./constants.json")
rolesPerCrewAndColor = json.load(f)
serveringServerId = int(os.environ.get("SERVERING_SERVER_ID"))
risingServerId = int(os.environ.get("RISING_SERVER_ID"))
knowingServerId = int(os.environ.get("KNOWING_SERVER_ID"))
racingServerId = int(os.environ.get("RACING_SERVER_ID"))


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
    if op=='kick':
        if ctx.permissions.kick_members == False:
            await ctx.send("<@"+str(ctx.author.id)+">, you're not authorized to kick members! Contact an admin/leader for this.")
            return
    elif op == 'ban' or op == 'unban':
        if ctx.permissions.ban_members == False:
            await ctx.send("<@"+str(ctx.author.id)+">, you're not authorized to ban/unban members! Contact an admin/leader for this.")
            return
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