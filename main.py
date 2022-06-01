# from nextcord import Locale

from nextcord import Locale

from general_imports import *
from cogs import server_setup, user_experience, battles, trade, achievements
from cogs.games import poker, tic_tac_toe

activity = nextcord.Activity(type=nextcord.ActivityType.listening, name="Древнерусский рейв")
intents = nextcord.Intents.default()
intents.members = True

EMOJIS_ID = {
    "Богатая семья": 955784319702548550,
    "Обычная семья": 955777557826002974,
    "Бедная семья": 955777604357603358,
    "Северяне": 955784315449532456,
    "Южане": 955784858897104916,
    "Техно-гики": 955784858804842506,
    "Валюта": 956604076739682304
}

bot = commands.Bot(
    intents=intents,
    debug_guilds=TEST_GUILDS_ID,
    command_prefix=PREFIX,
    activity=activity
)


@bot.event
async def on_ready():
    print(f"{bot.user} запустился!")

    for title, emoji_id in EMOJIS_ID.items():
        EMOJIS[title] = bot.get_emoji(emoji_id)


@bot.event
async def on_close():
    print("Closed")


@bot.event
async def on_message(message: nextcord.Message):
    user = message.author
    guild = message.guild

    if user.bot or get(guild.roles, name="Игрок") not in user.roles or \
            "/" in message.content or len(message.content) < 50:
        return

    await user_experience.add_xp(guild.id, user.id, 0.5)


@bot.event
async def on_member_join(member: nextcord.Member):
    user_id = f"{member.id}-{member.guild.id}"
    if not member.bot and not DB_SESSION.query(User).filter(User.id == user_id).first():
        user = User()
        user.id = user_id

        DB_SESSION.add(user)
    DB_SESSION.commit()


@bot.event
async def on_member_remove(member):
    User.query.filter(User.id == f"{member.id}-{member.guild.id}").delete()
    DB_SESSION.commit()


# battles.setup(bot)
user_experience.setup(bot)
achievements.setup(bot)
trade.setup(bot)
server_setup.setup(bot)
# poker.setup(bot)
tic_tac_toe.setup(bot)

bot.run(TOKEN)
