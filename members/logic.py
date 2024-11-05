import discord
import constants
import utils
from transfers import logic as transfers_logic


class Member:
    def __init__(
        self, admin: bool, leader: bool, member_id: int, name: str, multiple: int
    ):
        self.admin = admin
        self.leader = leader
        self.member_id = member_id
        self.name = name
        self.multiple = multiple


def sortFunction(member: Member):
    if member.leader:
        return "0 " + member.name
    if member.admin:
        return "1 " + member.name
    return "2 " + member.name


async def getPlayersResponse(ctx: discord.ApplicationContext, key: str):
    multipleAccountsData = constants.multipleAccountsCollection.find_one(
        {"key": key}, {"_id": 0}
    )
    if multipleAccountsData is not None:
        multipleAccountsIds = [key for key in multipleAccountsData if key != "key"]
    else:
        multipleAccountsIds = []
    crewData = constants.crewCollection.find_one({"key": key}, {"_id": 0}) or {}
    memberRoleId = utils.getDbField(constants.crewCollection, key, "member") or -1
    adminRoleId = utils.getDbField(constants.crewCollection, key, "admin") or -1
    leaderRoleId = utils.getDbField(constants.crewCollection, key, "leader") or -1
    if (
        not isinstance(memberRoleId, int)
        or not isinstance(adminRoleId, int)
        or not isinstance(leaderRoleId, int)
    ):
        return
    memberRole = utils.getRole(ctx, memberRoleId)
    adminRole = utils.getRole(ctx, adminRoleId)
    leaderRole = utils.getRole(ctx, leaderRoleId)
    if memberRole is None:
        return
    crewName = memberRole.name
    message = await utils.getMessage(
        ctx,
        crewData,
        "message_id",
        "members_channel_id",
        "**__Members for " + crewName.upper() + "__**",
    )
    guild = ctx.guild
    if guild is None:
        return
    response = getMembers(
        guild,
        crewName,
        adminRole,
        leaderRole,
        memberRole,
        multipleAccountsIds,
        multipleAccountsData,
    )
    response.sort(key=sortFunction)
    await transfers_logic.updateVacancies(ctx, key, response)

    stringResponse = "**__Members of " + crewName.upper() + "__**\n"
    number = 1
    for member in response:
        stringResponse += str(number) + ". <@!" + str(member.member_id) + ">"
        if member.multiple:
            stringResponse += " " + str(member.multiple)
        if member.leader:
            stringResponse += " -> **Leader**"
        elif member.admin:
            stringResponse += " -> *Admin*"
        stringResponse += "\n"
        number += 1
    if message is not None:
        await message.edit(content=stringResponse)
    return "OK, all good."


def getMembers(
    guild: discord.Guild,
    crewName: str,
    adminRole: discord.Role | None,
    leaderRole: discord.Role | None,
    memberRole: discord.Role,
    multipleAccountsIds,
    multipleAccountsData,
):
    response = []

    for member in guild.members:
        memberStruct = Member(False, False, member.id, member.display_name, 0)
        memberId = str(member.id)
        if adminRole is not None and member.get_role(adminRole.id):
            memberStruct.admin = True
        if leaderRole is not None and member.get_role(leaderRole.id):
            memberStruct.leader = True
        if member.get_role(memberRole.id):
            response.append(memberStruct)
        if memberId in multipleAccountsIds:
            if member.get_role(memberRole.id):
                for i in range(multipleAccountsData[memberId] - 1):
                    newMemberStruct = Member(
                        False, False, member.id, member.display_name, i + 2
                    )
                    response.append(newMemberStruct)
            else:
                constants.multipleAccountsCollection.update_one(
                    {"key": crewName}, {"$unset": {memberId: ""}}
                )
    return response


async def kickOrBanOrUnban(
    user: discord.Member, op: str, bot: discord.Bot, reason: str | None = None
):
    for guild in bot.guilds:
        if guild.id == constants.risingServerId:
            print(
                "Doing "
                + op
                + " for user: "
                + user.name
                + " in the server named: "
                + guild.name
            )
            if op == "kick":
                await guild.kick(user, reason=reason)
            elif op == "ban":
                await guild.ban(user, reason=reason)
            elif op == "unban":
                await guild.unban(user, reason=reason)


def processMultiple(user: discord.Member, crewName: str, numberOfAccounts: int):
    memberRoleId = utils.getDbField(constants.crewCollection, crewName, "member")
    if not isinstance(memberRoleId, int):
        return "Database error. Contact @AdrianG98RO for fixing it."
    if not user.get_role(memberRoleId):
        return "User does not have crew role! Add crew role and try again."
    memberId = str(user.id)
    if numberOfAccounts != 1:
        constants.multipleAccountsCollection.find_one_and_update(
            {"key": crewName}, {"$set": {memberId: numberOfAccounts}}, upsert=True
        )
    else:
        constants.multipleAccountsCollection.find_one_and_update(
            {"key": crewName}, {"$unset": {memberId: ""}}
        )
    return "Multiple accounts recorded!"
