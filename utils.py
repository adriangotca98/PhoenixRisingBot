from pymongo import collection
import time
import discord


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


def getRole(ctx: discord.ApplicationContext, roleName: str):
    if ctx.guild is None:
        return None
    for role in ctx.guild.roles:
        if role.name == roleName:
            return role
    return None


def getDbField(mongoCollection: collection.Collection, key: str, subkey: str):
    entry = mongoCollection.find_one({"key": key}, {"_id": 0, subkey: 1})
    if entry is None:
        return None
    if subkey not in entry.keys():
        return None
    return entry[subkey]


def getCrewNames(configCollection):
    crewNames = getDbField(configCollection, "crews", "value")
    if crewNames is None:
        return []
    crewNames.sort()
    return crewNames


def getCrewRegion(configCollection):
    return getDbField(configCollection, "crew_region", "value") or {}


def getCurrentSeason(configCollection):
    return int((time.time() - (getDbField(configCollection, 'time', 'value') or 0)) / 60 / 60 / 24 / 7 / 2) + 166
