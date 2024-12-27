import discord
import constants
import utils
import pymongo
from transfers import logic as transfers_logic
from members import logic as members_logic


class AddCrewLogic:
    def __init__(
        self,
        ctx: discord.ApplicationContext,
        region: str,
        shortname: str,
        longname: str,
    ):
        self.ctx = ctx
        self.guild: discord.Guild = self.ctx.guild
        self.region = region
        self.shortname = shortname
        self.longname = longname
        if self.shortname.count(" ") != 0:
            raise ValueError("Shortname cannot contain spaces.")
        if constants.crewCollection.find_one({"key": self.shortname}) != None:
            raise ValueError(
                "A crew with the same shortname already exists. That needs to be unique. You can check the shortnames by using multiple other commands. If you don't find the shortname in there, contact AdrianG98RO to check the DB directly."
            )
        if self.guild is None:
            raise ValueError("Error in getting the guild...")

    async def doWork(self) -> str:
        await self.__addRoles()
        await self.__addCategory()
        await self.__addChannels()
        constants.crewCollection.insert_one(
            {
                "key": self.shortname,
                "admin": self.adminRole.id,
                "member": self.memberRole.id,
                "leader": self.leaderRole.id,
                "leaderboard_id": self.leaderboardChannel.id,
                "members_channel_id": self.membersChannel.id,
                "admin_channel_id": self.adminChannel.id,
                "category_id": self.categoryChannel.id,
                "name": self.longname,
            }
        )
        self.__updateConfigData()
        await self.__updateVacanciesData()
        return f"Crew with shortname={self.shortname} and longname={self.longname} was successfully created, with entries in the DB, channels, category and roles. Feel free to use other commands on it from now on."

    async def __addRoles(self):
        memberRoleName = self.longname.capitalize()
        adminRoleName = self.shortname.capitalize() + " Admin"
        leaderRoleName = self.shortname.capitalize() + " Leader"
        permissions = self.__getPermissionsAndPositions()["permissions"]
        positions = self.__getPermissionsAndPositions()["positions"]
        setupDict = {
            "member": {
                "name": memberRoleName,
                "permissions": permissions["member"],
                "position": positions["member"],
            },
            "admin": {
                "name": adminRoleName,
                "permissions": permissions["admin"],
                "position": positions["admin"],
            },
            "leader": {
                "name": leaderRoleName,
                "permissions": permissions["leader"],
                "position": positions["leader"],
            },
        }
        self.memberRole = await self.__createAndMoveRole(setupDict["member"])
        self.adminRole = await self.__createAndMoveRole(setupDict["admin"])
        self.leaderRole = await self.__createAndMoveRole(setupDict["leader"])

    async def __createAndMoveRole(self, obj: dict):
        role: discord.Role = await self.guild.create_role(
            name=obj["name"],
            permissions=obj["permissions"],
            mentionable=True,
            hoist=True,
        )
        return await role.edit(position=obj["position"])

    async def __addCategory(self):
        belowCrewData = self.__getBelowCrewData()
        prefixes = (
            utils.getDbField(constants.configCollection, "crew_region", "prefixes")
            or {}
        )
        categoryPrefixes = (
            prefixes.get("category", {}) if isinstance(prefixes, dict) else {}
        )
        belowCategoryChannel = self.guild.get_channel(belowCrewData["category_id"])
        overwrites = self.__getOverwritesFromDust()
        if belowCategoryChannel is None:
            raise RuntimeError("Error in getting the below category channel...")
        name = constants.categoryCommon + " ".join(self.shortname.upper())
        name = categoryPrefixes[self.region] + name
        self.categoryChannel = await self.guild.create_category_channel(
            name, position=belowCategoryChannel.position - 1, overwrites=overwrites
        )
        if self.categoryChannel is None:
            raise RuntimeError("Error in creating the category channel...")

    async def __addChannels(self):
        overwrites = self.__getOverwritesFromDust("CHANNEL")
        await self.guild.create_text_channel(
            "🅒】" + self.shortname + "┃chat",
            category=self.categoryChannel,
            overwrites=overwrites,
        )
        self.membersChannel = await self.guild.create_text_channel(
            "🅜】" + self.shortname + "┃members", category=self.categoryChannel
        )
        await self.guild.create_text_channel(
            "🅘】" + self.shortname + "┃info", category=self.categoryChannel
        )
        await self.guild.create_text_channel(
            "🅟】" + self.shortname + "┃polls", category=self.categoryChannel
        )
        await self.guild.create_text_channel(
            "🅡】" + self.shortname + "┃records", category=self.categoryChannel
        )
        prefixes = (
            utils.getDbField(constants.configCollection, "crew_region", "prefixes")
            or {}
        )
        channelPrefixes = (
            prefixes.get("channel", {}) if isinstance(prefixes, dict) else {}
        )
        leaderboardPrefixes = (
            prefixes.get("leaderboard", {}) if isinstance(prefixes, dict) else {}
        )
        leadershipCategoryId = utils.getDbField(
            constants.configCollection, "IDs", "leadership_category_id"
        )
        leadershipCategoryId = (
            leadershipCategoryId if isinstance(leadershipCategoryId, int) else -1
        )
        leadershipCategory = self.guild.get_channel(leadershipCategoryId)
        leaderboardCategoryId = utils.getDbField(
            constants.configCollection, "IDs", "leaderboards_category_id"
        )
        leaderboardCategoryId = (
            leaderboardCategoryId if isinstance(leaderboardCategoryId, int) else -1
        )
        leaderboardCategory = self.guild.get_channel(leaderboardCategoryId)
        belowCrewData = self.__getBelowCrewData()
        belowCrewAdminChannel = self.guild.get_channel(
            belowCrewData["admin_channel_id"]
        )
        if (
            not isinstance(leadershipCategory, discord.CategoryChannel)
            or not isinstance(belowCrewAdminChannel, discord.TextChannel)
            or not isinstance(leaderboardCategory, discord.CategoryChannel)
        ):
            raise RuntimeError(
                "Error in getting the leadership category or below crew admin channel or leaderboard category..."
            )
        self.adminChannel = await self.guild.create_text_channel(
            channelPrefixes[self.region] + self.shortname + "┃leadership",
            category=leadershipCategory,
            position=belowCrewAdminChannel.position - 1,
        )
        self.leaderboardChannel = await self.guild.create_text_channel(
            leaderboardPrefixes[self.region] + "-" + self.shortname + "-0",
            category=leaderboardCategory,
        )

    def __getOverwritesFromDust(
        self,
        channelOrCategory: str = "CATEGORY",
    ):
        dustData = constants.crewCollection.find_one({"key": "dust"}) or {}
        dustCategoryId = dustData.get("category_id", -1)
        dustCategory = self.guild.get_channel(dustCategoryId)
        dustMemberRole = utils.getRole(self.ctx, dustData.get("member", -1))
        if (
            not isinstance(dustCategory, discord.CategoryChannel)
            or dustMemberRole is None
        ):
            return {}
        dustChatChannel = list(
            filter(lambda channel: channel.name.endswith("chat"), dustCategory.channels)
        )[0]
        categoryOverwrites = dustCategory.overwrites
        categoryOverwrites[self.memberRole] = categoryOverwrites[dustMemberRole]
        del categoryOverwrites[dustMemberRole]
        channelOverwrites = dustChatChannel.overwrites
        channelOverwrites[self.memberRole] = channelOverwrites[dustMemberRole]
        del channelOverwrites[dustMemberRole]
        if channelOrCategory == "CHANNEL":
            return channelOverwrites
        return categoryOverwrites

    def __updateConfigData(self):
        constants.configCollection.update_one(
            {"key": "crews"}, {"$push": {"value": self.shortname}}
        )
        constants.configCollection.update_one(
            {"key": "crew_region"}, {"$push": {f"value.{self.region}": self.shortname}}
        )

    async def __updateVacanciesData(self):
        constants.vacanciesCollection.update_one(
            {}, {"$set": {self.shortname: {"current": 0, "next": 0}}}
        )
        await transfers_logic.updateVacancies(self.ctx, self.shortname)

    def __getBelowCrewData(self):
        return (
            constants.crewCollection.find_one(
                {
                    "$and": [
                        {"key": {"$gt": self.shortname}},
                        {"key": {"$ne": "fire"}},
                        {"key": {"$ne": "ice"}},
                    ]
                },
                sort={"key": pymongo.ASCENDING},
            )
            or {}
        )

    def __getPermissionsAndPositions(self) -> dict:
        crewData = constants.crewCollection.find_one()
        if not isinstance(crewData, dict):
            raise ValueError("Crew data not found.")

        memberRoleId, adminRoleId, leaderRoleId = (
            crewData["member"],
            crewData["admin"],
            crewData["leader"],
        )
        memberRole, adminRole, leaderRole = (
            utils.getRole(self.ctx, memberRoleId),
            utils.getRole(self.ctx, adminRoleId),
            utils.getRole(self.ctx, leaderRoleId),
        )
        if memberRole is None or adminRole is None or leaderRole is None:
            raise ValueError("Roles not found.")
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


class RemoveCrewLogic:
    def __init__(self, ctx: discord.ApplicationContext, shortname: str):
        self.ctx = ctx
        self.shortname = shortname
        self.guild: discord.Guild = self.ctx.guild
        if self.guild is None:
            raise ValueError("Error in getting the guild...")
        self.crewData = constants.crewCollection.find_one({"key": self.shortname})
        if self.crewData is None:
            raise ValueError("Crew not in the db...")

    async def doWork(self) -> str:
        await self.__deleteChannelsAndCategoryAndRoles()
        constants.vacanciesCollection.update_one({}, {"$unset": {self.shortname: ""}})
        constants.multipleAccountsCollection.delete_one({"key": self.shortname})
        constants.configCollection.update_one(
            {"key": "crews"}, {"$pull": {"value": self.shortname}}
        )
        constants.configCollection.update_one(
            {"key": "crew_region"},
            {
                "$pull": {
                    "value.EU": self.shortname,
                    "value.US": self.shortname,
                    "value.AUS/JPN": self.shortname,
                }
            },
        )
        constants.crewCollection.delete_one({"key": self.shortname})
        await self.__deleteMoves()
        return f"All good. Crew {self.shortname} was deleted from DB, as well as channels and roles."

    async def __deleteEntity(self, key: str, getFunction):
        id = self.crewData[key]
        channelOrCategoryOrRole = getFunction(id)
        if channelOrCategoryOrRole is None:
            return
        if isinstance(channelOrCategoryOrRole, discord.CategoryChannel):
            for channel in channelOrCategoryOrRole.channels:
                await channel.delete()
        await channelOrCategoryOrRole.delete()

    async def __deleteChannelsAndCategoryAndRoles(self):
        await self.__deleteEntity("category_id", self.guild.get_channel)
        await self.__deleteEntity("leaderboard_id", self.guild.get_channel)
        await self.__deleteEntity("admin_channel_id", self.guild.get_channel)
        await self.__deleteEntity("admin", self.guild.get_role)
        await self.__deleteEntity("leader", self.guild.get_role)
        await self.__deleteEntity("member", self.guild.get_role)

    async def __deleteMoves(self):
        moves = list(
            constants.movesCollection.find(
                {"$or": [{"crew_from": self.shortname}, {"crew_to": self.shortname}]}
            )
        )
        constants.movesCollection.delete_many(
            {"$or": [{"crew_from": self.shortname}, {"crew_to": self.shortname}]}
        )
        alteredCrews = set()
        for move in moves:
            if move["crew_from"] == self.shortname:
                await transfers_logic.deleteMovementFromMessage(
                    self.ctx, move["crew_from"], "OUT"
                )
                alteredCrews.add(move["crew_from"])
            else:
                await transfers_logic.deleteMovementFromMessage(
                    self.ctx, move["crew_to"], "IN"
                )
                alteredCrews.add(move["crew_to"])
        for crew in alteredCrews:
            await transfers_logic.updateVacancies(self.ctx, crew)
        await transfers_logic.updateVacancies(
            self.ctx, utils.getCrewNames(constants.configCollection)[0]
        )


class EditCrewLogic:
    def __init__(
        self,
        ctx: discord.ApplicationContext,
        crew: str,
        fieldToEdit: str,
        newValue: str,
    ):
        self.ctx = ctx
        self.crew = crew
        self.fieldToEdit = fieldToEdit
        self.newValue = newValue
        self.guild: discord.Guild = self.ctx.guild
        if self.guild is None:
            raise ValueError("Error in getting the guild...")
        self.crewData = constants.crewCollection.find_one({"key": self.crew})
        if self.crewData is None:
            raise ValueError("Crew not in the db...")

    async def doWork(self):
        if self.fieldToEdit == "Short crew name":
            await self.__editShortName()
        elif self.fieldToEdit == "Long crew name":
            self.__editLongName()
        elif self.fieldToEdit == "Wildcard schedule link":
            self.__editWildcardScheduleLink()
        elif self.fieldToEdit == "Min RP":
            self.__editMinRP()
        return f"All good. Crew {self.crew} was edited in the DB, as well as the appropriate entities on the server, if needed."

    def __editWildcardScheduleLink(self):
        constants.crewCollection.update_one(
            {"key": self.crew}, {"$set": {"wildcard": self.newValue}}
        )

    def __editMinRP(self):
        constants.crewCollection.update_one(
            {"key": self.crew}, {"$set": {"min_rp": self.newValue}}
        )

    async def __editShortName(self):
        if self.newValue.count(" ") != 0:
            raise ValueError("Shortname cannot contain spaces.")
        if constants.crewCollection.find_one({"key": self.newValue}) != None:
            raise ValueError(
                "A crew with the same shortname already exists. That needs to be unique. You can check the shortnames by using multiple other commands. If you don't find the shortname in there, contact AdrianG98RO to check the DB directly."
            )
        regionKey = f"value.{utils.getRegionKey(self.crew)}"
        self.__updateCrewData()
        self.__updateConfigData(regionKey)
        await self.__updateMovesAndVacancies()
        await self.__editChannelNames()

    async def __updateMovesAndVacancies(self):
        constants.multipleAccountsCollection.update_one(
            {"key": self.crew}, {"$set": {"key": self.newValue}}
        )
        constants.movesCollection.update_many(
            {"crew_from": self.crew}, {"$set": {"crew_from": self.newValue}}
        )
        constants.movesCollection.update_many(
            {"crew_to": self.crew}, {"$set": {"crew_to": self.newValue}}
        )
        constants.vacanciesCollection.update_one(
            {}, {"$rename": {self.crew: self.newValue}}
        )
        await transfers_logic.updateVacancies(
            self.ctx, utils.getCrewNames(constants.configCollection)[0]
        )
        await members_logic.getPlayersResponse(self.ctx, self.newValue)

    def __updateCrewData(self):
        constants.crewCollection.update_one(
            {"key": self.crew}, {"$set": {"key": self.newValue}}
        )

    def __updateConfigData(self, regionKey: str):
        constants.configCollection.update_one(
            {"key": "crew_region"},
            {
                "$pull": {
                    regionKey: self.crew,
                }
            },
        )
        constants.configCollection.update_one(
            {"key": "crew_region"},
            {
                "$push": {
                    regionKey: self.newValue,
                }
            },
        )
        constants.configCollection.update_one(
            {"key": "crews"}, {"$pull": {"value": self.crew}}
        )
        constants.configCollection.update_one(
            {"key": "crews"}, {"$push": {"value": self.newValue}}
        )

    async def __editChannelNames(self):
        categoryChannel = self.guild.get_channel(self.crewData["category_id"])
        if isinstance(categoryChannel, discord.CategoryChannel):
            for channel in categoryChannel.channels:
                await channel.edit(name=channel.name.replace(self.crew, self.newValue))

        channels = [
            self.crewData["leaderboard_id"],
            self.crewData["admin_channel_id"],
            self.crewData["members_channel_id"],
        ]

        for channel_id in channels:
            channel = self.guild.get_channel(channel_id)
            if channel:
                await channel.edit(name=channel.name.replace(self.crew, self.newValue))

    def __editLongName(self):
        constants.crewCollection.update_one(
            {"key": self.crew}, {"$set": {"name": self.newValue}}
        )


class GetCrewLogic:
    def __init__(self, ctx: discord.ApplicationContext, crew: str):
        self.ctx = ctx
        self.crew = crew

    async def doWork(self):
        message = ""
        if self.crew in utils.getCrewNames(constants.configCollection):
            return self.__getMessageForSingleCrew(True)
        else:
            regions = utils.getCrewRegion(constants.configCollection)
            for region in regions.keys():
                message += f"# __{region.upper()} Crews__\n\n"
                for crew in regions[region]:
                    self.crew = crew
                    message += self.__getMessageForSingleCrew(False)
            return message

    def __getMessageForSingleCrew(self, addLeadership):
        return f"""## {utils.getDbField(constants.crewCollection, self.crew, "name")}
{self.__maybeAddLeadership(addLeadership)}
- Wildcard Link: {self.__getWildcardLink()}
- RP Min: {self.__getMinRP()}
"""

    def __maybeAddLeadership(self, addLeadership):
        if addLeadership:
            return f"""- Leader: {self.__getLeader()}
- Admins: 
{self.__getAdmins()}"""
        return ""

    def __getLeader(self):
        leaderRole = utils.getRole(
            self.ctx, utils.getDbField(constants.crewCollection, self.crew, "leader")
        )
        return f"<@{leaderRole.members[0].id}>"

    def __getAdmins(self):
        adminRole = utils.getRole(
            self.ctx, utils.getDbField(constants.crewCollection, self.crew, "admin")
        )
        return "\n".join(map(lambda member: f"  - <@{member.id}>", adminRole.members))

    def __getWildcardLink(self):
        return utils.getDbField(constants.crewCollection, self.crew, "wildcard") or "-"

    def __getMinRP(self):
        return utils.getDbField(constants.crewCollection, self.crew, "min_rp") or "-"
