import discord
import constants
import utils
import pymongo
from transfers import logic as transfers_logic


async def addCrew(
    ctx: discord.ApplicationContext, region: str, shortname: str, longname: str
) -> str:
    if constants.crewCollection.find_one({"key": shortname}) != None:
        return "A crew with the same shortname already exists. That needs to be unique. You can check the shortnames by using multiple other commands. If you don't find the shortname in there, contact AdrianG98RO to check the DB directly."
    if shortname.count(" ") != 0:
        return "Shortname must not contain whispaces."
    result = await addRoles(ctx, shortname, longname)
    if result is None:
        return "Error in adding roles..."
    memberRole, adminRole, leaderRole = result
    if memberRole is None or adminRole is None or leaderRole is None:
        return "Error in creating roles..."
    categoryChannel = await addCategory(ctx, region, shortname, memberRole)
    if categoryChannel is None:
        return "Error in creating the category channel..."
    result = await addChannels(ctx, shortname, region, categoryChannel, memberRole)
    if result is None:
        return "Error in adding channels..."
    membersChannel, adminChannel, leaderboardChannel = result
    constants.crewCollection.insert_one(
        {
            "key": shortname,
            "admin": adminRole.id,
            "member": memberRole.id,
            "leader": leaderRole.id,
            "leaderboard_id": leaderboardChannel.id,
            "members_channel_id": membersChannel.id,
            "admin_channel_id": adminChannel.id,
            "category_id": categoryChannel.id,
            "name": longname,
        }
    )
    constants.configCollection.update_one(
        {"key": "crews"}, {"$push": {"value": shortname}}
    )
    constants.configCollection.update_one(
        {"key": "crew_region"}, {"$push": {f"value.{region}": shortname}}
    )
    constants.vacanciesCollection.update_one(
        {}, {"$set": {shortname: {"current": 0, "next": 0}}}
    )
    await transfers_logic.updateVacancies(ctx, shortname)
    return f"Crew with shortname={shortname} and longname={longname} was successfully created, with entries in the DB, channels, category and roles. Feel free to use other commands on it from now on."


async def deleteEntity(crewData: dict, key: str, getFunction):
    id = crewData[key]
    channelOrCategoryOrRole = getFunction(id)
    if channelOrCategoryOrRole is None:
        return
    if isinstance(channelOrCategoryOrRole, discord.CategoryChannel):
        for channel in channelOrCategoryOrRole.channels:
            await channel.delete()
    await channelOrCategoryOrRole.delete()


async def deleteChannelsAndCategoryAndRoles(guild: discord.Guild, crewData: dict):
    await deleteEntity(crewData, "category_id", guild.get_channel)
    await deleteEntity(crewData, "leaderboard_id", guild.get_channel)
    await deleteEntity(crewData, "admin_channel_id", guild.get_channel)
    await deleteEntity(crewData, "admin", guild.get_role)
    await deleteEntity(crewData, "leader", guild.get_role)
    await deleteEntity(crewData, "member", guild.get_role)


async def deleteMoves(ctx: discord.ApplicationContext, shortname: str):
    moves = list(
        constants.movesCollection.find(
            {"$or": [{"crew_from": shortname}, {"crew_to": shortname}]}
        )
    )
    constants.movesCollection.delete_many(
        {"$or": [{"crew_from": shortname}, {"crew_to": shortname}]}
    )
    alteredCrews = set()
    for move in moves:
        if move["crew_from"] == shortname:
            await transfers_logic.deleteMovementFromMessage(
                ctx, move["crew_from"], "OUT"
            )
            alteredCrews.add(move["crew_from"])
        else:
            await transfers_logic.deleteMovementFromMessage(ctx, move["crew_to"], "IN")
            alteredCrews.add(move["crew_to"])
    for crew in alteredCrews:
        await transfers_logic.updateVacancies(ctx, crew)
    await transfers_logic.updateVacancies(
        ctx, utils.getCrewNames(constants.configCollection)[0]
    )


async def removeCrew(ctx: discord.ApplicationContext, shortname: str):
    crewData = constants.crewCollection.find_one({"key": shortname})
    if not isinstance(crewData, dict):
        return "Crew not in the dn..."
    guild = ctx.guild
    if not isinstance(guild, discord.Guild):
        return
    await deleteChannelsAndCategoryAndRoles(guild, crewData)
    constants.vacanciesCollection.update_one({}, {"$unset": {shortname: ""}})
    constants.multipleAccountsCollection.delete_one({"key": shortname})
    constants.configCollection.update_one(
        {"key": "crews"}, {"$pull": {"value": shortname}}
    )
    constants.configCollection.update_one(
        {"key": "crew_region"},
        {
            "$pull": {
                "value.EU": shortname,
                "value.US": shortname,
                "value.AUS/JPN": shortname,
            }
        },
    )
    constants.crewCollection.delete_one({"key": shortname})
    await deleteMoves(ctx, shortname)
    return f"All good. Crew {shortname} was deleted from DB, as well as channels and roles."


async def editCrew(*args):
    return "Not implemented yet."


async def addRoles(ctx: discord.ApplicationContext, shortname: str, longname: str):
    memberRoleName = longname.capitalize()
    adminRoleName = shortname.capitalize() + " Admin"
    leaderRoleName = shortname.capitalize() + " Leader"
    guild = ctx.guild
    permissions = getPermissionsAndPositions(ctx)["permissions"]
    positions = getPermissionsAndPositions(ctx)["positions"]
    if permissions is None or guild is None or positions is None:
        return
    memberRole = await createAndMoveRole(
        guild, memberRoleName, permissions["member"], positions["member"]
    )
    adminRole = await createAndMoveRole(
        guild, adminRoleName, permissions["admin"], positions["admin"]
    )
    leaderRole = await createAndMoveRole(
        guild, leaderRoleName, permissions["leader"], positions["leader"]
    )
    return memberRole, adminRole, leaderRole


async def addCategory(
    ctx: discord.ApplicationContext,
    region: str,
    shortname: str,
    memberRole: discord.Role,
):
    guild = ctx.guild
    if guild is None:
        return
    belowCrewData = getBelowCrewData(shortname)
    prefixes = (
        utils.getDbField(constants.configCollection, "crew_region", "prefixes") or {}
    )
    categoryPrefixes = prefixes.get("category") if isinstance(prefixes, dict) else {}
    belowCategoryChannel = guild.get_channel(belowCrewData["category_id"])
    overwrites = getOverwritesFromDust(ctx, guild, memberRole)
    if not isinstance(categoryPrefixes, dict) or belowCategoryChannel is None:
        return
    name = constants.categoryCommon + " ".join(shortname.upper())
    name = categoryPrefixes[region] + name
    return await guild.create_category_channel(
        name, position=belowCategoryChannel.position - 1, overwrites=overwrites
    )


async def addChannels(
    ctx: discord.ApplicationContext,
    shortname: str,
    region: str,
    categoryChannel: discord.CategoryChannel,
    memberRole: discord.Role,
):
    guild = ctx.guild
    if guild is None:
        return
    overwrites = getOverwritesFromDust(ctx, guild, memberRole, "CHANNEL")
    await guild.create_text_channel(
        "🅒】" + shortname + "┃chat", category=categoryChannel, overwrites=overwrites
    )
    membersChannel = await guild.create_text_channel(
        "🅜】" + shortname + "┃members", category=categoryChannel
    )
    await guild.create_text_channel(
        "🅘】" + shortname + "┃info", category=categoryChannel
    )
    await guild.create_text_channel(
        "🅟】" + shortname + "┃polls", category=categoryChannel
    )
    await guild.create_text_channel(
        "🅡】" + shortname + "┃records", category=categoryChannel
    )
    prefixes = (
        utils.getDbField(constants.configCollection, "crew_region", "prefixes") or {}
    )
    channelPrefixes = (
        prefixes.get("channel") if isinstance(prefixes, dict) else {}
    ) or {}
    leaderboardPrefixes = (
        prefixes.get("leaderboard") if isinstance(prefixes, dict) else {}
    ) or {}
    leadershipCategoryId = utils.getDbField(
        constants.configCollection, "IDs", "leadership_category_id"
    )
    leadershipCategoryId = (
        leadershipCategoryId if isinstance(leadershipCategoryId, int) else -1
    )
    leadershipCategory = guild.get_channel(leadershipCategoryId)
    leaderboardCategoryId = utils.getDbField(
        constants.configCollection, "IDs", "leaderboards_category_id"
    )
    leaderboardCategoryId = (
        leaderboardCategoryId if isinstance(leaderboardCategoryId, int) else -1
    )
    leaderboardCategory = guild.get_channel(leaderboardCategoryId)
    belowCrewData = getBelowCrewData(shortname)
    belowCrewAdminChannel = guild.get_channel(belowCrewData["admin_channel_id"])
    if (
        not isinstance(leadershipCategory, discord.CategoryChannel)
        or not isinstance(belowCrewAdminChannel, discord.TextChannel)
        or not isinstance(leaderboardCategory, discord.CategoryChannel)
    ):
        return
    adminChannel = await guild.create_text_channel(
        channelPrefixes[region] + shortname + "┃leadership",
        category=leadershipCategory,
        position=belowCrewAdminChannel.position - 1,
    )
    leaderboardChannel = await guild.create_text_channel(
        leaderboardPrefixes[region] + "-" + shortname + "-0",
        category=leaderboardCategory,
    )
    return membersChannel, adminChannel, leaderboardChannel


def getOverwritesFromDust(
    ctx: discord.ApplicationContext,
    guild: discord.Guild,
    memberRole: discord.Role,
    channelOrCategory: str = "CATEGORY",
):
    dustData = constants.crewCollection.find_one({"key": "dust"}) or {}
    dustCategoryId = dustData.get("category_id", -1)
    dustCategory = guild.get_channel(dustCategoryId)
    dustMemberRole = utils.getRole(ctx, dustData.get("member", -1))
    if not isinstance(dustCategory, discord.CategoryChannel) or dustMemberRole is None:
        return {}
    dustChatChannel = list(
        filter(lambda channel: channel.name.endswith("chat"), dustCategory.channels)
    )[0]
    categoryOverwrites = dustCategory.overwrites
    categoryOverwrites[memberRole] = categoryOverwrites[dustMemberRole]
    del categoryOverwrites[dustMemberRole]
    channelOverwrites = dustChatChannel.overwrites
    channelOverwrites[memberRole] = channelOverwrites[dustMemberRole]
    del channelOverwrites[dustMemberRole]
    if channelOrCategory == "CHANNEL":
        return channelOverwrites
    return categoryOverwrites


def getBelowCrewData(shortname: str):
    return (
        constants.crewCollection.find_one(
            {
                "$and": [
                    {"key": {"$gt": shortname}},
                    {"key": {"$ne": "fire"}},
                    {"key": {"$ne": "ice"}},
                ]
            },
            sort={"key": pymongo.ASCENDING},
        )
        or {}
    )


def getPermissionsAndPositions(ctx: discord.ApplicationContext) -> dict:
    crewData = constants.crewCollection.find_one()
    if not isinstance(crewData, dict):
        return {"permissions": None, "positions": None}
    memberRoleId, adminRoleId, leaderRoleId = (
        crewData["member"],
        crewData["admin"],
        crewData["leader"],
    )
    memberRole, adminRole, leaderRole = (
        utils.getRole(ctx, memberRoleId),
        utils.getRole(ctx, adminRoleId),
        utils.getRole(ctx, leaderRoleId),
    )
    if memberRole is None or adminRole is None or leaderRole is None:
        return {"permissions": None, "positions": None}
    return {
        "permissions": {
            "member": memberRole.permissions,
            "admin": adminRole.permissions,
            "leader": leaderRole.permissions,
        },
        "positions": {
            "member": memberRole.position + 1,
            "admin": adminRole.position + 1,
            "leader": leaderRole.position + 1,
        },
    }


async def createAndMoveRole(
    guild: discord.Guild, roleName: str, permissions: discord.Permissions, position: int
):
    memberRole = await guild.create_role(
        name=roleName, permissions=permissions, mentionable=True, hoist=True
    )
    return await memberRole.edit(position=position)
