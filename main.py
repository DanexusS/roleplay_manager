import os
from general_imports import *

# TODO: добавить больше игр
# TODO: перенести на новую версию весь код
# TODO: добавить новую /help команду взамен старой

activity = nextcord.Activity(type=nextcord.ActivityType.listening, name="Древнерусский рейв")
intents = nextcord.Intents.default()
intents.members = True

bot = commands.Bot(
    intents=intents,
    debug_guilds=TEST_GUILDS_ID,
    command_prefix=PREFIX,
    activity=activity
)

for cog in os.listdir("./cogs/"):
    if os.path.isfile(f"./cogs/{cog}"):
        bot.load_extension(f"cogs.{cog[:-3]}")
    elif cog != "__pycache__":
        for sub_cog in os.listdir(f"./cogs/{cog}/"):
            if os.path.isfile(f"./cogs/{cog}/{sub_cog}"):
                bot.load_extension(f"cogs.{cog}.{sub_cog[:-3]}")

# TODO: добавить более надёжную защиту токенов и не только
bot.run(TOKEN)
