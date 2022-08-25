# This example requires the 'members' and 'message_content' privileged intents to function.

import os
import discord
from discord.ext import commands
import json

description = '''Phoenix Rising family bot, Fawkes.'''

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

@bot.command(name='i_sol')
async def solInit(ctx):
    await sendInitMessage(ctx,'AETERNUM SOL','Sol')

@bot.command(name='i_ignis')
async def ignisInit(ctx):
    await sendInitMessage(ctx,'AETERNUM IGNIS','Ignis')

@bot.command(name='i_dust')
async def dustInit(ctx):
    await sendInitMessage(ctx,'FROM THE DUST','Dust')

@bot.command(name='i_ashes')
async def ashesInit(ctx):
    await sendInitMessage(ctx,'FROM THE ASHES','Ashes')

@bot.command(name='i_reborn')
async def RebornInit(ctx):
    await sendInitMessage(ctx,'PHOENIX REBORN','Reborn')

@bot.command(name='i_risen')
async def RisenInit(ctx):
    await sendInitMessage(ctx,'PHOENIX RISEN','Risen')

@bot.command(name='i_helios')
async def heliosInit(ctx):
    await sendInitMessage(ctx,'PHOENIX HELIOS','Helios')

@bot.command(name='i_nova')
async def novaInit(ctx):
    await sendInitMessage(ctx,'PHOENIX NOVA','Nova')

@bot.command(name='i_vulcan')
async def vulcanInit(ctx):
    await sendInitMessage(ctx,'PHOENIX VULCAN','Vulcan')

@bot.command(name='i_nebula')
async def nebulaInit(ctx):
    await sendInitMessage(ctx,'PHOENIX NEBULA','Nebula')

@bot.command(name='i_titan')
async def titanInit(ctx):
    await sendInitMessage(ctx,'PHOENIX TITAN','Titan')

@bot.command(name='i_bootes')
async def bootesInit(ctx):
    await sendInitMessage(ctx,'BOOTES VOID','Bootes')

@bot.command(name='i_ice')
async def iceInit(ctx):
    await sendInitMessage(ctx,'PHOENIX ICE','Ice')

@bot.command(name='i_fire')
async def fireInit(ctx):
    await sendInitMessage(ctx,'PHOENIX FIRE','Fire')

@bot.command(name='i_dragon')
async def dragonInit(ctx):
    await sendInitMessage(ctx,'PHOENIX DRAGON','Dragon')

@bot.command(name='i_astra')
async def australasiaInit(ctx):
    await sendInitMessage(ctx,'PHOENIX AUSTRALASIA','Astra')

@bot.command(name='i_kraken')
async def krakenInit(ctx):
    await sendInitMessage(ctx,'PHOENIX KRAKEN','Kraken')

@bot.command(name='m_fire')
async def firePlayers(ctx):
    await getPlayersResponse(ctx, rolesPerCrewAndColor['Fire'], "Phoenix Fire")

@bot.command(name='m_sol')
async def solPlayers(ctx):
    await getPlayersResponse(ctx, rolesPerCrewAndColor['Sol'], 'Aeternum Sol')

@bot.command(name='m_dust')
async def dustPlayers(ctx):
    await getPlayersResponse(ctx, rolesPerCrewAndColor['Dust'], "From The Dust")

@bot.command(name='m_risen')
async def risenPlayers(ctx):
    await getPlayersResponse(ctx, rolesPerCrewAndColor['Risen'], "Phoenix Risen")

@bot.command(name='m_dragon')
async def dragonPlayers(ctx):
    await getPlayersResponse(ctx, rolesPerCrewAndColor['Dragon'], "Phoenix Dragon")

@bot.command(name='m_helios')
async def heliosPlayers(ctx):
    await getPlayersResponse(ctx, rolesPerCrewAndColor['Helios'], "Phoenix Helios")

@bot.command(name='m_vulcan')
async def vulcanPlayers(ctx):
    await getPlayersResponse(ctx, rolesPerCrewAndColor['Vulcan'], "Phoenix Vulcan")

@bot.command(name='m_bootes')
async def bootesPlayers(ctx):
    await getPlayersResponse(ctx, rolesPerCrewAndColor['Bootes'], "Bootes Void")

@bot.command(name='m_ice')
async def icePlayers(ctx):
    await getPlayersResponse(ctx, rolesPerCrewAndColor['Ice'], "Phoenix Ice")

@bot.command(name='m_ignis')
async def ignisPlayers(ctx):
    await getPlayersResponse(ctx, rolesPerCrewAndColor['Ignis'], "Aeternum Ignis")

@bot.command(name='m_ashes')
async def ashesPlayers(ctx):
    await getPlayersResponse(ctx, rolesPerCrewAndColor['Ashes'], "From The Ashes")

@bot.command(name='m_nebula')
async def nebulaPlayers(ctx):
    await getPlayersResponse(ctx, rolesPerCrewAndColor['Nebula'], "Phoenix Nebula")

@bot.command(name='m_nova')
async def novaPlayers(ctx):
    await getPlayersResponse(ctx, rolesPerCrewAndColor['Nova'], "Phoenix Nova")

@bot.command(name='m_reborn')
async def rebornPlayers(ctx):
    await getPlayersResponse(ctx, rolesPerCrewAndColor['Reborn'], "Phoenix Reborn")

@bot.command(name='m_titan')
async def titanPlayers(ctx):
    await getPlayersResponse(ctx, rolesPerCrewAndColor['Titan'], "Phoenix Titan")

@bot.command(name='m_kraken')
async def krakenPlayers(ctx):
    await getPlayersResponse(ctx, rolesPerCrewAndColor['Kraken'], "Phoenix Kraken")

@bot.command(name='m_astra')
async def australasiaPlayers(ctx):
    await getPlayersResponse(ctx, rolesPerCrewAndColor['AustralAsia'], "Phoenix AustralAsia")

async def sendInitMessage(ctx, crewNameCaps, crewName):
    message = await ctx.send("**__Members for "+crewNameCaps+"__**")
    rolesPerCrewAndColor[crewName]['messageId'] = message.id
    await ctx.message.delete()

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
    await ctx.message.delete()


bot.run(os.environ.get("DISCORD_BOT_TOKEN"))