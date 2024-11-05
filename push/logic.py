import discord
import constants

def startPush(role: discord.Role, membersChannel: discord.TextChannel, chatChannel: discord.TextChannel, crewName: str):
    constants.configCollection.update_one({"key": "crews"}, {"$push": {"value": crewName}})
    constants.configCollection.update_one({"key": "crew_region"},  {"$push": {f"value.PUSH": crewName}})
    constants.vacanciesCollection.update_one({}, {"$set": {crewName: {"current": 0, "next": 0}}})
    constants.crewCollection.insert_one({
        "member": role.id,
        "key": crewName,
        "members_channel_id": membersChannel.id,
        "chat_channel_id": chatChannel.id
    })
    return "Push registered successfully."


def endPush(crewName):
    constants.configCollection.update_one({"key": "crews"}, {"$pull": {"value": crewName}})
    constants.configCollection.update_one({"key": "crew_region"},  {"$pull": {f"value.PUSH": crewName}})
    constants.vacanciesCollection.update_one({}, {"$unset": {crewName: ""}})
    constants.crewCollection.delete_one({"key": crewName})
    return "Push crew removed from tracking successfully."
