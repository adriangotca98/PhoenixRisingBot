from pymongo import MongoClient
import utils

configFile = open("config.txt", "r")
config = configFile.read()
username = config.split("\n")[0]
mongo_password = config.split("\n")[1]
client = MongoClient(
    f"mongodb+srv://{username}:{mongo_password}@phoenixrisingcluster.p2zno6x.mongodb.net"
    f"/?retryWrites=true"
    f"&w=majority"
)
crewCollection = client.get_database("Fawkes").get_collection("crewData")
configCollection = client.get_database("Fawkes").get_collection("configData")
multipleAccountsCollection = client.get_database("Fawkes").get_collection(
    "multipleAccountsData"
)
movesCollection = client.get_database("Fawkes").get_collection("movesData")
vacanciesCollection = client.get_database("Fawkes").get_collection("vacanciesData")
scores = {}
discord_bot_token = utils.getDbField(configCollection, "discord_token", "value") or ""
risingServerId = utils.getDbField(configCollection, "IDs", "rising_server_id") or -1
loggingChannelId = utils.getDbField(configCollection, "IDs", "logging_channel_id")
loggingChannelId = loggingChannelId if isinstance(loggingChannelId, int) else -1
hallChannelId = utils.getDbField(configCollection, "IDs", "hall_channel_id")
hallChannelId = hallChannelId if isinstance(hallChannelId, int) else -1
vacanciesChannelId = utils.getDbField(configCollection, "IDs", "vacancies_channel_id")
vacanciesChannelId = vacanciesChannelId if isinstance(vacanciesChannelId, int) else -1
vacanciesMessageId = utils.getDbField(configCollection, "IDs", "vacancies_message_id")
vacanciesMessageId = vacanciesMessageId if isinstance(vacanciesMessageId, int) else -1
communityMemberRoleId = utils.getDbField(
    configCollection, "IDs", "community_member_role_id"
)
communityMemberRoleId = (
    communityMemberRoleId if isinstance(communityMemberRoleId, int) else -1
)
categoryCommon = utils.getDbField(configCollection, "IDs", "category_common")
categoryCommon = categoryCommon if isinstance(categoryCommon, str) else ""
commandsList = [
    "ban",
    "cancel_transfer",
    "current_season",
    "kick",
    "make_transfers",
    "members",
    "multiple",
    "score",
    "transfer",
    "unban",
]
commandsMessages = {
    "add_crew_part_1": "# Add crew, part 1\nAdd category for the channels of the crew and region of the crew.",
    "add_crew_part_2": "Enter the short name of the crew (e.g. ice)",
    "ban": "# Banning Time!\nSelect user to ban from the server below:",
    "cancel_transfer": "# Cancel Transfer?\nIf you wish to cancel an input transfer, complete the following fields and submit:",
    "current_season": lambda: f"# Current Season\nWe are currently in season {utils.getCurrentSeason(configCollection)}",
    "end_push": "# End push\nEnds and stops tracking for a push crew. Does not delete channels or roles, nor modify people roles.",
    "kick": "# Booting Time!\nSelect user you would like to kick from the server below:",
    "make_transfers": "# Make Transfers?\nUpon confirming, Fawkes will complete all crew transfers for the current season. Are you sure?",
    "members": "# Member List Update\nChoose a crew from the list below to update its current members count:",
    "multiple": "# Multi-Account Register\nChoose a user below to change how many accounts they have in a given crew:",
    "remove_crew": "# Remove Crew\nChoose the crew to remove from Fawkes. ATTENTION! This will DELETE the channels and roles related to it, and this operation is IRREVERSIBLE!",
    "score": "# Crew Score\nSelect a crew below to update its end of season score:",
    "start_push_part_1": "# Start a push\nStarts tracking for a push crew, with a few arguments needed below:",
    "start_push_part_2": "Give the crew name (Shown name):",
    "transfer": lambda: f"# Player Transfer\nComplete the below fields to register an upcoming player transfer (please note that current season is {utils.getCurrentSeason(configCollection)}):",
    "unban": "# Undo Ban\nInput the discord name of a user you wish to lift a ban from:",
}
