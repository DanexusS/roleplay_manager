from nextcord.ext import commands

from constants import *
from cogs import server_setup, user_experience, battles, trade
from cogs.games import poker, tic_tac_toe

activity = nextcord.Activity(type=nextcord.ActivityType.listening, name="Древнерусский рейв")
intents = nextcord.Intents.default()
intents.members = True

bot = commands.Bot(intents=intents, debug_guilds=TEST_GUILDS_ID, command_prefix=PREFIX, activity=activity)


@bot.event
async def on_ready():
    print(f"{bot.user} запустился!")


@bot.event
async def on_member_join(member: nextcord.Member):
    user_id = f"{member.id}-{member.guild.id}"
    if not member.bot and not db_sess.query(User).filter(User.id == user_id).first():
        user = User()
        user.id = user_id

        db_sess.add(user)
    db_sess.commit()


@bot.event
async def on_member_remove(member):
    User.query.filter(User.id == f"{member.id}-{member.guild.id}").delete()
    db_sess.commit()


# battles.setup(bot)
user_experience.setup(bot)
trade.setup(bot)
server_setup.setup(bot)
poker.setup(bot)
tic_tac_toe.setup(bot)

bot.run(TOKEN)
