from pymongo import collection
import time
import discord

import constants

def updateSelect(select: discord.ui.Select):
    for idx in range(len(select.options)):
        select.options[idx].default = False
        if select.options[idx].label == select.values[0]:
            select.options[idx].default = True
    return select

def resetSelect(view: discord.ui.View, *args):
    index = 0
    for child in view.children:
        if isinstance(child, discord.ui.Select):
            child.options = list(
                map(
                    lambda name: discord.SelectOption(label=name, default=False),
                    args[index]
                )
            )
            index += 1

def getCrewField(crew, editField):
    dbField = "key" if editField is "Short crew name" else "name"
    crewObj = constants.crewCollection.find_one({"key": crew})
    if crewObj is None:
        return None
    return crewObj[dbField]

def computeScoreFromChannelName(name: str) -> int:
    number = ""
    for char in name:
        if char.isnumeric():
            number += char
    return int(number)

def getPushCrewNames(crewCollection: collection.Collection) -> list[str]:
    crews = list(map(lambda entry: entry.get("key"), crewCollection.find({"leaderboard_id": {"$exists": False}}, {"key": True})))
    return crews

def getScoreWithSeparator(intScore: int) -> str:
    scoreWithSeparator = ""
    while intScore > 0:
        number = str(intScore % 1000)
        while len(number) < 3:
            number = "0" + number
        scoreWithSeparator = "’" + number + scoreWithSeparator
        intScore //= 1000
    while scoreWithSeparator[0] == "0" or scoreWithSeparator[0] == "’":
        scoreWithSeparator = scoreWithSeparator[1:]
    return scoreWithSeparator

def getRole(ctx: discord.ApplicationContext, roleId: int) -> discord.Role | None:
    if ctx.guild is None:
        return None
    return ctx.guild.get_role(roleId)

def getDbField(
    mongoCollection: collection.Collection, key: str, subkey: str
) -> str | int | list | dict | None:
    entry = mongoCollection.find_one({"key": key}, {"_id": 0, subkey: 1})
    if entry is None:
        return None
    if subkey not in entry.keys():
        return None
    return entry.get(subkey)

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
    timestamp = getDbField(configCollection, "time", "value")
    if not isinstance(timestamp, int):
        timestamp = 0
    return int((time.time() - (timestamp or 0)) / 60 / 60 / 24 / 7 / 2) + 166
