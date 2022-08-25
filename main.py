# This example requires the 'members' and 'message_content' privileged intents to function.

import os
import discord
from discord.ext import commands
import json

description = '''An example bot to showcase the discord.ext.commands extension
module.
There are a number of utility commands being showcased here.'''

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='?', description=description, intents=intents)
f = open("./constants.json")
rolesPerCrewAndColor = json.load(f)

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

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

@bot.command()
async def solInit(ctx):
    message = await ctx.send("Members for Aeternum Sol")
    rolesPerCrewAndColor['Sol']['messageId'] = message.id

@bot.command()
async def ignisInit(ctx):
    message = await ctx.send("Members for Aeternum Ignis")
    rolesPerCrewAndColor['Ignis']['messageId'] = message.id

@bot.command()
async def dustInit(ctx):
    message = await ctx.send("Members for From The Dust")
    rolesPerCrewAndColor['Dust']['messageId'] = message.id

@bot.command()
async def ashesInit(ctx):
    message = await ctx.send("Members for From The Ashes")
    rolesPerCrewAndColor['Ashes']['messageId'] = message.id

@bot.command()
async def RebornInit(ctx):
    message = await ctx.send("Members for Phoenix Reborn")
    rolesPerCrewAndColor['Reborn']['messageId'] = message.id

@bot.command()
async def RisenInit(ctx):
    message = await ctx.send("Members for Phoenix Risen")
    rolesPerCrewAndColor['Risen']['messageId'] = message.id

@bot.command()
async def heliosInit(ctx):
    message = await ctx.send("Members for Phoenix Helios")
    rolesPerCrewAndColor['Helios']['messageId'] = message.id

@bot.command()
async def novaInit(ctx):
    message = await ctx.send("Members for Phoenix Nova")
    rolesPerCrewAndColor['Nova']['messageId'] = message.id

@bot.command()
async def vulcanInit(ctx):
    message = await ctx.send("Members for Phoenix Vulcan")
    rolesPerCrewAndColor['Vulcan']['messageId'] = message.id

@bot.command()
async def nebulaInit(ctx):
    message = await ctx.send("Members for Phoenix Nebula")
    rolesPerCrewAndColor['Nebula']['messageId'] = message.id

@bot.command()
async def titanInit(ctx):
    message = await ctx.send("Members for Phoenix Titan")
    rolesPerCrewAndColor['Sol']['messageId'] = message.id

@bot.command()
async def bootesInit(ctx):
    message = await ctx.send("Members for Bootes Void")
    rolesPerCrewAndColor['Bootes']['messageId'] = message.id

@bot.command()
async def iceInit(ctx):
    message = await ctx.send("Members for Phoenix Ice")
    rolesPerCrewAndColor['Ice']['messageId'] = message.id

@bot.command()
async def fireInit(ctx):
    message = await ctx.send("Members for Phoenix Fire")
    rolesPerCrewAndColor['Fire']['messageId'] = message.id

@bot.command()
async def dragonInit(ctx):
    message = await ctx.send("Members for Phoenix Dragon")
    rolesPerCrewAndColor['Dragon']['messageId'] = message.id

@bot.command()
async def australasiaInit(ctx):
    message = await ctx.send("Members for Phoenix AustralAsia")
    rolesPerCrewAndColor['AustralAsia']['messageId'] = message.id

@bot.command()
async def krakenInit(ctx):
    message = await ctx.send("Members for Phoenix Kraken")
    rolesPerCrewAndColor['Kraken']['messageId'] = message.id

@bot.command()
async def firePlayers(ctx):
    await getPlayersResponse(ctx, rolesPerCrewAndColor['Fire'], "Phoenix Fire")

@bot.command()
async def solPlayers(ctx):
    await getPlayersResponse(ctx, rolesPerCrewAndColor['Sol'], 'Aeternum Sol')

@bot.command()
async def dustPlayers(ctx):
    await getPlayersResponse(ctx, rolesPerCrewAndColor['Dust'], "From The Dust")

@bot.command()
async def risenPlayers(ctx):
    await getPlayersResponse(ctx, rolesPerCrewAndColor['Risen'], "Phoenix Risen")

@bot.command()
async def dragonPlayers(ctx):
    await getPlayersResponse(ctx, rolesPerCrewAndColor['Dragon'], "Phoenix Dragon")

@bot.command()
async def heliosPlayers(ctx):
    await getPlayersResponse(ctx, rolesPerCrewAndColor['Helios'], "Phoenix Helios")

@bot.command()
async def vulcanPlayers(ctx):
    await getPlayersResponse(ctx, rolesPerCrewAndColor['Vulcan'], "Phoenix Vulcan")

@bot.command()
async def bootesPlayers(ctx):
    await getPlayersResponse(ctx, rolesPerCrewAndColor['Bootes'], "Bootes Void")

@bot.command()
async def icePlayers(ctx):
    await getPlayersResponse(ctx, rolesPerCrewAndColor['Ice'], "Phoenix Ice")

@bot.command()
async def ignisPlayers(ctx):
    await getPlayersResponse(ctx, rolesPerCrewAndColor['Ignis'], "Aeternum Ignis")

@bot.command()
async def ashesPlayers(ctx):
    await getPlayersResponse(ctx, rolesPerCrewAndColor['Ashes'], "From The Ashes")

@bot.command()
async def nebulaPlayers(ctx):
    await getPlayersResponse(ctx, rolesPerCrewAndColor['Nebula'], "Phoenix Nebula")

@bot.command()
async def novaPlayers(ctx):
    await getPlayersResponse(ctx, rolesPerCrewAndColor['Nova'], "Phoenix Nova")

@bot.command()
async def rebornPlayers(ctx):
    await getPlayersResponse(ctx, rolesPerCrewAndColor['Reborn'], "Phoenix Reborn")

@bot.command()
async def titanPlayers(ctx):
    await getPlayersResponse(ctx, rolesPerCrewAndColor['Titan'], "Phoenix Titan")

@bot.command()
async def krakenPlayers(ctx):
    await getPlayersResponse(ctx, rolesPerCrewAndColor['Kraken'], "Phoenix Kraken")

@bot.command()
async def australasiaPlayers(ctx):
    await getPlayersResponse(ctx, rolesPerCrewAndColor['AustralAsia'], "Phoenix AustralAsia")

async def getPlayersResponse(ctx, rolesAndColor, crewName):
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
    
    stringResponse = 'Members of '+crewName+"\n"
    number = 1
    for member in response:
        stringResponse+=str(number) + ". <@!"+str(member.id)+">"
        if member.leader:
            stringResponse+=" -> Leader"
        elif member.admin:
            stringResponse+=" -> Admin"
        stringResponse+='\n'
        number+=1
    
    message = await ctx.fetch_message(rolesAndColor['messageId'])
    await message.edit(content = stringResponse)
    embed = discord.Embed(color=int(rolesAndColor['color'],base=16),title = "Members of "+crewName, description=stringResponse)
    
    # await ctx.send(stringResponse,allowed_mentions = discord.AllowedMentions(replied_user=False))


bot.run(os.environ.get("DISCORD_BOT_TOKEN"))