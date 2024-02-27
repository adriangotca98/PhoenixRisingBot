from pymongo import collection
import time
import discord


def computeScoreFromChannelName(name: str) -> int:
    number = ''
    for char in name:
        if char.isnumeric():
            number += char
    return int(number)


def getScoreWithSeparator(intScore: int) -> str:
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


def getRole(ctx: discord.ApplicationContext, roleId: int) -> discord.Role | None:
    if ctx.guild is None:
        return None
    return ctx.guild.get_role(roleId)


def getDbField(mongoCollection: collection.Collection, key: str, subkey: str) -> str | int | list | dict | None:
    entry = mongoCollection.find_one({"key": key}, {"_id": 0, subkey: 1})
    if entry is None:
        return None
    if subkey not in entry.keys():
        return None
    return entry[subkey]


def getCrewNames(configCollection) -> list:
    crewNames = getDbField(configCollection, "crews", "value")
    if crewNames is None:
        return []
    if not isinstance(crewNames, list):
        return []
    crewNames.sort()
    return crewNames


def getCrewRegion(configCollection) -> dict:
    entry = getDbField(configCollection, "crew_region", "value")
    if not isinstance(entry, dict):
        return {}
    return entry


def getCurrentSeason(configCollection) -> int:
    timestamp = getDbField(configCollection, 'time', 'value')
    if not isinstance(timestamp, int):
        timestamp = 0
    return int((time.time() - (timestamp or 0)) / 60 / 60 / 24 / 7 / 2) + 166
