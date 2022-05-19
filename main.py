from nextcord.ext import commands

from constants import *
from cogs import server_setup, poker, user_experience, battles, trade

activity = nextcord.Activity(type=nextcord.ActivityType.listening, name="Древнерусский рейв")
intents = nextcord.Intents.default()
intents.members = True

bot = commands.Bot(intents=intents, debug_guilds=TEST_GUILDS_ID, command_prefix=PREFIX, activity=activity)


@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")


@bot.event
async def on_member_join(member: nextcord.Member):
    user_id = f"{member.id}-{member.guild.id}"
    if not member.bot and not db_sess.query(User).filter(User.id == user_id).first():
        user = User()
        user.id = user_id
        user.name = '-1'
        user.nation = '-1'
        user.origin = '-1'
        user.balance = 0
        user.level = 1
        user.xp = 0
        user.skill_points = 0
        user.health = 5
        user.strength = 5
        user.intelligence = 5
        user.dexterity = 5
        user.speed = 5
        user.inventory = ''
        user.equipped_inventory = ''

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

bot.run(TOKEN)
