import discord
import json
from discord.ext import commands, tasks
from discord.utils import get
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_option


TOKEN = "NTY3MzMyNTU5NDc5MTExNzQw.XLR_ng.zhaxoAo_6ZL-LfA5gBEZXPAfGj0"
PREFIX = "/"
test_servers_id = [936293335063232672]
activity = discord.Activity(type=discord.ActivityType.listening, name="шутки про хохлов")
client = commands.Bot(command_prefix=PREFIX, activity=activity)
slash = SlashCommand(client, sync_commands=True)


@client.event
async def on_ready():
    print("Бот запустился")


# ----------------------------------------ПРИМЕР-КОМАНД----------------------------------------
# @slash.slash(
#     name="hi",
#     description="says hi",
#     guild_ids=[server_id]
# )
# async def hi(ctx):
#     await ctx.send(f"{client.get_emoji(951508751771369523)}Hello")
#
#
# @slash.slash(
#     name="hi_member",
#     description="says hi1",
#     options=[{"name": "member", "description": "пользователь", "type": 6, "required": True}],
#     guild_ids=[server_id]
# )
# async def hi_member(ctx, member: discord.Member = None):
#     await ctx.send(f"Hello {member.mention}")
# ----------------------------------------------------------------------------------------------


# Команда, настраивающая сервер
@slash.slash(
    name="implement",
    description="Создаёт чаты и настраивает сервер для игры!",
    guild_ids=test_servers_id
)
async def implement(ctx):
    guild = ctx.guild
    await guild.create_text_channel('cool-channel')
    await ctx.send(f"Готово!")


# Запуск
client.run(TOKEN)
