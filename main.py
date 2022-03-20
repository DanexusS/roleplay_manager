import discord
import json

from data import *
from discord.ext import commands
from discord.utils import get
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_option
from discord_components import DiscordComponents, Button, ButtonStyle


test_servers_id = [936293335063232672]
activity = discord.Activity(type=discord.ActivityType.listening, name="шутки про хохлов")
client = commands.Bot(command_prefix=PREFIX, activity=activity)
slash = SlashCommand(client, sync_commands=True)


@client.event
async def on_ready():
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
            await ctx.send(f":x: Чат регистрации уже создан.")
            return

    channel = await guild.create_text_channel(name)

    await channel.send(f"**В этом чате вы должны создать своего персонажа.** *подходите к этому вопросу с умом!*")

    # ======= ВЫБОР РАСЫ
    text = '*```yaml\n➢ От расы зависят некоторые характеристики.\n➢ [Дописать что то ещё].```*'
    emb = discord.Embed(title='⮮ __**Выбор расы:**__', color=44444)
    emb.add_field(name='**Важно:**', value=text, inline=False)

    await channel.send(
        embed=emb,
        components=[
            [Button(style=ButtonStyle.gray, label="Северяне", emoji=client.get_emoji(emoji["north"])),
             Button(style=ButtonStyle.gray, label="Южнане", emoji=client.get_emoji(emoji["south"])),
             Button(style=ButtonStyle.gray, label="Техно-гики", emoji=client.get_emoji(emoji["techno"]))]
        ]
    )
    # ======= ВЫБОР ПРОИСХОЖДЕНИЯ
    text = '*```yaml\n➢ От происхождения зависят некоторые характеристики.\n➢ [Дописать что то ещё].```*'
    emb = discord.Embed(title='⮮ __**Выбор происхождения:**__', color=44444)
    emb.add_field(name='**Важно:**', value=text, inline=False)

    await channel.send(
        embed=emb,
        components=[
            [Button(style=ButtonStyle.gray, label="Богатая семья", emoji=client.get_emoji(emoji["rich"])),
             Button(style=ButtonStyle.gray, label="Обычная семья", emoji=client.get_emoji(emoji["norm"])),
             Button(style=ButtonStyle.gray, label="Бедность", emoji=client.get_emoji(emoji["poor"]))]
        ]
    )
    # ======= СОЗДАНИЕ ИМЕНИ
    text = '*```yaml\n' \
           '➢ Желаемое вами имя напишите в данный чат.\n' \
           '➢ Имя не влияет на характеристики.\n' \
           '➢ Вводите имя с умом так как его нельзя будет изменить.```*'
    emb = discord.Embed(title='⮮ __**Ваше имя:**__', color=44444)
    emb.add_field(name='**Важно:**', value=text, inline=False)

    await channel.send(embed=emb)

    # Сделать создание имени

    # ======= ПРОЧЕЕ
    ''' РАБОТАЕТ НЕ ТАК КАК НАДО
    response = await client.wait_for("button_click")
    if response.channel == channel:
        if response.component.label == "Северяне":
            await response.respond(content="Great!")
        else:
            await response.respond(content="Not cool!")
    '''

    await ctx.send(f":white_check_mark: Чат регистрации создан.")


# КОМАНДА, настраивающая сервер
@slash.slash(
    name="implement",
    description="Создаёт чаты и настраивает сервер для игры!",
    guild_ids=test_servers_id
)
async def implement(ctx):
    await create_registration(ctx)

    await ctx.send(f":white_check_mark: **Готово!**")


# Запуск
DiscordComponents(client)
client.run(TOKEN)
