import discord
import json
from discord.ext import commands
from discord.utils import get
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_option
from discord_components import DiscordComponents, Button, ButtonStyle


TOKEN = "NTY3MzMyNTU5NDc5MTExNzQw.XLR_ng.zhaxoAo_6ZL-LfA5gBEZXPAfGj0"
PREFIX = "/"
test_servers_id = [936293335063232672]
activity = discord.Activity(type=discord.ActivityType.listening, name="шутки про хохлов")
client = commands.Bot(command_prefix=PREFIX, activity=activity)
slash = SlashCommand(client, sync_commands=True)


@client.event
async def on_ready():
    DiscordComponents(client)
    print("Бот запустился")


# ----------------------------------------ПРИМЕР-КОМАНДЫ----------------------------------------
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

# @bot.event
# async def on_button_click(inter):
#
#     res = 'Вы успешно верифицировались!' # ваш вывод сообщение что человек получил роль
#     guild = bot.get_guild(inter.guild.id)
#
#     if inter.component.id == "verif_button":
#         verif = guild.get_role(id вашей роли)
#         member = inter.author
#         await member.add_roles(verif)
#         await inter.reply(res, ephemeral = True)


# КОМАНДА, создающая чат с регистрацией
async def create_registration(ctx):
    guild = ctx.guild
    name = 'создание-персонажа'
    for channel in guild.channels:
        if channel.name == name:
            await ctx.send(f"Чат регистрации уже создан.")
            return

    channel = await guild.create_text_channel(name)

    await channel.send(
        components=[
            [Button(style=ButtonStyle.gray, label="кто нажмёт, тот лох", emoji="👋"),
             Button(style=ButtonStyle.green, label="кто нажмёт, тот не лох", emoji="👋")]
        ]
    )
    response = await client.wait_for("button_click")
    if response.channel == ctx.channel:
        if response.component.label == "кто нажмёт, тот лох":
            await response.respond(content="Great!")
        else:
            await response.respond(content="Not cool!")

    await channel.send(f"Создан чат регистрации.")


# КОМАНДА, настраивающая сервер
@slash.slash(
    name="implement",
    description="Создаёт чаты и настраивает сервер для игры!",
    guild_ids=test_servers_id
)
async def implement(ctx):
    await create_registration(ctx)

    await ctx.send(f"Готово!")


# Запуск
client.run(TOKEN)
