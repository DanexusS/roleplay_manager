import discord
import json
import os

from consts import *
from discord.ext import commands
from discord.utils import get
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_option
from discord_components import DiscordComponents, Button, ButtonStyle
from data import db_session
from data.users import User


test_servers_id = [936293335063232672]

activity = discord.Activity(type=discord.ActivityType.listening, name="шутки про хохлов")
intents = discord.Intents.default()
intents.members = True

client = commands.Bot(command_prefix=PREFIX, intents=intents, activity=activity)
slash = SlashCommand(client, sync_commands=True)

for db in DataBase:
    db_session.global_init(f"db/{db}.db")
db_sess = db_session.create_session()


# ФУНКЦИЯ, показывающая то что бот запустился
@client.event
async def on_ready():
    print("Бот запустился")

# ----------------------------------------ПРИМЕР-КОМАНДЫ----------------------------------------
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
# ----------------------------------------ПРИМЕР-КОМАНДЫ----------------------------------------


# ФУНКЦИЯ, обрабатывающая нажатие кнопок
@client.event
async def on_button_click(interaction):
    decision_type = interaction.component.label
    member = interaction.user
    if decision_type in group_lbl_button_nation:
        user = db_sess.query(User).filter(User.id == member.id).first()
        user.nation = decision_type
        await interaction.send(f"*Теперь вы пренадлежите расе **{decision_type}**!* [Это сообщение можно удалить]")
    if decision_type in group_lbl_button_origin:
        user = db_sess.query(User).filter(User.id == member.id).first()
        user.origin = decision_type
        await interaction.send(f"*Теперь вы из \"**{decision_type}**\"!* [Это сообщение можно удалить]")
    db_sess.commit()


# ФУНКЦИЯ, создающая категорию "Общее"
async def create_category(guild, title):
    return await guild.create_category(title)


# # ФУНКЦИЯ, создающая чат с регистрацией
# async def create_registration(ctx, guild, role, category):
#     channel = await guild.create_text_channel(group_name_channels_1[0], category=category)
#     await channel.set_permissions(role, send_messages=False, read_message_history=False, read_messages=False)
#
#
#
#     # # ======= ПРОЧЕЕ
#     # await ctx.send(f":white_check_mark: Чат регистрации создан.")


# # ФУНКЦИЯ, создающая
# async def create_info(ctx, guild, role, category):
#     channel = await guild.create_text_channel(group_name_channels_1[1], category=category)
#     await channel.set_permissions(guild.default_role, send_messages=False, read_message_history=False, read_messages=False)
#     await channel.set_permissions(role, send_messages=True, read_message_history=True, read_messages=True)
#
#     # # ======= ПРОЧЕЕ
#     # await ctx.send(f":white_check_mark: Чат информации создан.")


# # ФУНКЦИЯ, создающая магазин
# async def create_shop(ctx, guild, role, category):
#     channel = await guild.create_text_channel(group_name_channels_1[2], category=category)
#     await channel.set_permissions(guild.default_role, send_messages=False, read_message_history=False, read_messages=False)
#     await channel.set_permissions(role, send_messages=True, read_message_history=True, read_messages=True)
#
#     # # ======= ПРОЧЕЕ
#     # await ctx.send(f":white_check_mark: Магазин создан.")


# # ФУНКЦИЯ, создающая город 1 (тест)
# async def create_category_city(ctx):
#     pass


# ФУНКЦИЯ, записывающая всех в базу данных и создающая роль определяющая создан ли профиль
async def create_db(guild):
    for member in guild.members:
        if not member.bot:
            user = User()
            user.id = member.id
            user.name = '-1'
            user.nation = '-1'
            user.origin = '-1'
            user.money = -1
            user.health = -1
            user.strength = -1
            user.intelligence = -1
            user.dexterity = -1
            user.speed = -1
            user.inventory = 'item;item'
            db_sess.add(user)
    db_sess.commit()


async def create_channel(guild, channel_info, category, title, player_role):
    kind, allow_messaging = channel_info
    channel = await guild.create_text_channel(title, category=category)

    await channel.set_permissions(guild.default_role,
                                  send_messages=allow_messaging,
                                  read_messages=kind != "game" or kind == "all")
    await channel.set_permissions(player_role,
                                  send_messages=allow_messaging,
                                  read_messages=kind == "game" or kind == "all")

    return channel


async def send_registration_msg(channel):
    await channel.send(f"**В этом чате вы должны создать своего персонажа.** *Подходите к этому вопросу с умом!*")

    # ======= ВЫБОР РАСЫ
    text = '*```yaml\n' \
           '➢ От расы зависят некоторые характеристики.\n' \
           '➢ Пока вы не завершите создание профиля вы можете перевыбирать расу.```*'
    emb = discord.Embed(title='⮮ __**Выбор расы:**__', color=44444)
    emb.add_field(name='**Важно:**', value=text, inline=False)

    await channel.send(
        embed=emb,
        components=[
            [Button(style=ButtonStyle.gray, label=group_lbl_button_nation[0], emoji=client.get_emoji(emoji["north"])),
             Button(style=ButtonStyle.gray, label=group_lbl_button_nation[1], emoji=client.get_emoji(emoji["south"])),
             Button(style=ButtonStyle.gray, label=group_lbl_button_nation[2], emoji=client.get_emoji(emoji["techno"]))]
        ]
    )
    # ======= ВЫБОР ПРОИСХОЖДЕНИЯ
    text = '*```yaml\n' \
           '➢ От происхождения зависят некоторые характеристики.\n' \
           '➢ Пока вы не завершите создание профиля вы можете перевыбирать происхождение.```*'
    emb = discord.Embed(title='⮮ __**Выбор происхождения:**__', color=44444)
    emb.add_field(name='**Важно:**', value=text, inline=False)

    await channel.send(
        embed=emb,
        components=[
            [Button(style=ButtonStyle.gray, label=group_lbl_button_origin[0], emoji=client.get_emoji(emoji["rich"])),
             Button(style=ButtonStyle.gray, label=group_lbl_button_origin[1], emoji=client.get_emoji(emoji["norm"])),
             Button(style=ButtonStyle.gray, label=group_lbl_button_origin[2], emoji=client.get_emoji(emoji["poor"]))]
        ]
    )
    # ======= СОЗДАНИЕ ИМЕНИ
    text = '*```yaml\n' \
           '➢ Желаемое вами имя напишите в данный чат с помощью команды: "/name".\n' \
           '➢ Имя не влияет на характеристики.\n' \
           '➢ Вводите имя с умом так как его можно будет изменить только через админа.' \
           '➢ После написания имени вы завершите создание профиля.```*'
    emb = discord.Embed(title='⮮ __**Ваше имя:**__', color=44444)
    emb.add_field(name='**Важно:**', value=text, inline=False)

    await channel.send(embed=emb)


# КОМАНДА, настраивающая сервер
@slash.slash(
    name="implement",
    description="Создаёт чаты и настраивает сервер для игры!",
    guild_ids=test_servers_id
)
async def implement(ctx):
    guild = ctx.guild
    player_role = await guild.create_role(name="Игрок", color=44444)

    # Создание чатов
    for category, channels in objects.items():
        _category = await create_category(guild, category)
        for channel in channels.keys():
            discord_channel = await create_channel(guild, channels[channel].values(), _category, channel, player_role)
            if discord_channel.name == "создание-персонажа":
                await send_registration_msg(discord_channel)

    # Создание специальной роли и бд
    await create_db(guild)
    await ctx.send(":white_check_mark: **Готово!**")
    # role = get(guild.roles, name="Игрок")
    # # Создание общей категории
    # category = await create_category_main(ctx, guild)
    # # Создание регистрации
    # await create_registration(ctx, guild, role, category)
    # # Создание чата информации
    # await create_info(ctx, guild, role, category)
    # # Создание магазина
    # await create_shop(ctx, guild, role, category)
    # # # Создание города 1 (тест)
    # # await create_category_city(ctx)
    # # Уведомление о том что всё готово

# # КОМАНДА,
# @slash.slash(
#     name="reset",
#     description="Удаляет чаты и настройку  сервера для игры!",
#     guild_ids=test_servers_id
# )
# async def reset(ctx):
#     guild = ctx.guild
#     # Список чатов категорий и тд
#     objects = [
#         get(guild.channels, name=group_name_channels_1[0]), get(guild.channels, name=group_name_channels_1[1]),
#         get(guild.channels, name=group_name_channels_1[2]), get(guild.roles, name="Игрок"),
#         get(guild.categories, name=group_name_categories[0])
#     ]
#     # Удаление чатов категорий и тд
#     for obj in objects:
#         if obj:
#             await obj.delete()
#     # Удаление базы данных
#     for db in DataBase:
#         os.remove(f"db/{db}.db")
#     # Уведомление о том что всё готово
#     await ctx.send(f":white_check_mark: **Готово!**")

# КОМАНДА, добавляющая ник и создающая профиль
@client.command()
async def name(ctx, *args):
    await ctx.message.delete()

    member = ctx.author
    _name = ' '.join(args)
    user = db_sess.query(User).filter(User.id == member.id).first()

    for role in member.roles:
        if role.name == 'Игрок':
            await member.send('**Вы не можете поменять своё имя!** *Для этого обратитесь к администрации.*')
            return
    if user.nation == '-1' or user.origin == '-1':
        await member.send('**Вы не можете создать профиль не выбрав ни расу, ни происхождение!**')
        return

    user.name = _name
    db_sess.commit()
    # Добавляется роль @Игрок
    role = get(ctx.guild.roles, name="Игрок")
    await member.add_roles(role)


@slash.slash(
    name="open_inventory",
    description="Открыть инвентарь персонажа",
    guild_ids=test_servers_id
)
# КОМАНДА, открывающая инвентарь
async def inventory(ctx):
    player = ctx.author
    user = db_sess.query(User).filter(User.id == player.id).first()

    print(user)

    emb = discord.Embed(title="Инвентарь", color=0xFFFFF0)
    emb.add_field(name="------------", value="112", inline=False)

    await ctx.send(embed=emb)

# Запуск
DiscordComponents(client)
client.run(TOKEN)
