import discord
from discord.ext import commands
from discord.utils import get
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_option


TOKEN = "NTY3MzMyNTU5NDc5MTExNzQw.XLR_ng.zhaxoAo_6ZL-LfA5gBEZXPAfGj0"
PREFIX = "/"
server_id = 936293335063232672
client = commands.Bot(command_prefix=PREFIX)
slash = SlashCommand(client, sync_commands=True)


@client.event
async def on_ready():
    print("Бот запустился")


@slash.slash(
    name="hi",
    description="says hi",
    guild_ids=[server_id]
)
async def hi(ctx):
    await ctx.send("Hello")

client.run(TOKEN)
