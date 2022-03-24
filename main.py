import discord
import json
import os

from consts import *
from discord.ext import commands
from discord.ext.commands import MissingPermissions, MissingRole, CommandInvokeError
from discord.utils import get
from discord_slash import SlashCommand
from discord_components import DiscordComponents, Button, ButtonStyle
from data import db_session
from data.users import User


test_servers_id = [936293335063232672]

activity = discord.Activity(type=discord.ActivityType.listening, name="шутки про хохлов")
intents = discord.Intents.default()
intents.members = True

client = commands.Bot(command_prefix=PREFIX, intents=intents, activity=activity)
slash = SlashCommand(client, sync_commands=True)

db_session.global_init(f"db/DataBase.db")
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


# ФУНКЦИЯ, создающая категории
async def create_category(guild, title):
    return await guild.create_category(title)


# ФУНКЦИЯ, записывающая всех в базу данных
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
            user.inventory = 'item;item;item1;item;item1;item1'
            db_sess.add(user)
    db_sess.commit()


# ФУНКЦИЯ, отправляющаю сообщение в чат регистрации
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


# ФУНКЦИЯ, создающая чаты
async def create_channel(guild, channel_info, category, title, roles_for_permss):
    kind, allow_messaging = channel_info
    channel = await guild.create_text_channel(title, category=category)

    if kind != 'all':
        for name, role in roles_for_permss.items():
            await channel.set_permissions(role,
                                          send_messages=allow_messaging,
                                          read_messages=kind == name)

    return channel


# КОМАНДА, настраивающая сервер
@client.command()
@commands.has_guild_permissions(administrator=True)
async def implement(ctx):
    await ctx.message.delete()
    guild = ctx.guild
    # Роль обозначающая, что пользователь создал профиль
    player_role = await guild.create_role(name="Игрок", color=44444)
    # Роли обозначающии в каком городе игрок
    topolis_role = await guild.create_role(name="Тополис", color=16777215)
    braifast_role = await guild.create_role(name="Браифаст", color=16777215)
    jadiff_role = await guild.create_role(name="Джадифф", color=16777215)

    roles_for_permss = {
        "non-game": guild.default_role,
        "game": player_role,
        "city_topolis": topolis_role,
        "city_braifast": braifast_role,
        "city_jadiff": jadiff_role
    }

    # Создание чатов
    for category, channels in objects.items():
        _category = await create_category(guild, category)
        for channel in channels.keys():
            channel = await create_channel(guild, channels[channel].values(), _category, channel, roles_for_permss)
            if channel.name == "создание-персонажа":
                await send_registration_msg(get(guild.channels, name="создание-персонажа"))

    # Создание бд
    await create_db(guild)
    await ctx.send(":white_check_mark: **Готово!**")


# КОМАНДА, удаляющая всё не нужное
@client.command()
@commands.has_guild_permissions(administrator=True)
async def reset(ctx):
    await ctx.message.delete()
    guild = ctx.guild
    # Удаление чатов категорий и тд
    discord_objects = []
    for category, channels in objects.items():
        discord_objects.append(get(guild.categories, name=category))
        for channel in channels.keys():
            discord_objects.append(get(guild.channels, name=channel))
    for role in roles_game:
        discord_objects.append(get(guild.roles, name=role))

    for discord_object in discord_objects:
        if discord_object:
            await discord_object.delete()

    # Удаление базы данных
    try:
        os.remove(f"db/DataBase.db")
    except FileNotFoundError:
        print('База данных не найдена!')
    # Уведомление о том что всё готово
    await ctx.send(":white_check_mark: **Готово!**")


# КОМАНДА, добавляющая ник и создающая профиль
@client.command()
async def name(ctx, *args):
    await ctx.message.delete()

    if ctx.channel.id != get(ctx.guild.channels, name="создание-персонажа").id:
        return

    member = ctx.author
    _name = ' '.join(args)
    user = db_sess.query(User).filter(User.id == member.id).first()

    for role in member.roles:
        if role.name == 'Игрок':
            await member.send('**Вы не можете поменять своё имя!** *Для этого обратитесь к администрации.*')
            return
    if user.nation == '-1' or user.origin == '-1':
        await member.send('**Вы не можете создать профиль не выбрав расу или происхождение!**')
        return

    user.name = _name
    db_sess.commit()
    # Добавляется роль @Игрок
    role = get(ctx.guild.roles, name="Игрок")
    await member.add_roles(role)


# КОМАНДА, добавить предмет
@slash.slash(
    name="add_item",
    description="Отправить предложение обмена другому игроку",
    options=[{"name": "item", "description": "предмет", "type": 3, "required": True}],
    guild_ids=test_servers_id
)
async def add_item(ctx, item):
    player = ctx.author
    db_sess.query(User).filter(User.id == player.id).first().inventory += f"{item};"
    db_sess.commit()
    await ctx.send("Done")


# КОМАНДА, трейд
@slash.slash(
    name="trade",
    description="Отправить предложение обмена другому игроку",
    options=[{"name": "member", "description": "пользователь", "type": 6, "required": True}],
    guild_ids=test_servers_id
)
@commands.has_role("Игрок")
async def trade(ctx, member):
    player = ctx.author
    if player == member or member.bot:
        await throw_error(ctx, 100)
        return
    user = db_sess.query(User).filter(User.id == player.id).first()
    player_inventory = {}
    for item in user.inventory.split(";"):
        player_inventory[item] = player_inventory.get(item, 0) + 1

    emb = discord.Embed(title="**Ваш инвентарь**", color=0xFFFFF0)
    buttons = [[]]

    for item in player_inventory:
        buttons[0].append(Button(style=ButtonStyle.gray, label=f"{item} x{player_inventory[item]}"))

    await ctx.send(f"Выберете предметы из своего инвентаря и из инвентаря {member.mention}")
    await ctx.channel.send(embed=emb, components=buttons)

    user = db_sess.query(User).filter(User.id == member.id).first()
    player_inventory = {}
    for item in user.inventory.split(";"):
        player_inventory[item] = player_inventory.get(item, 0) + 1

    emb = discord.Embed(title=f"**Инвентарь игрока {member.name}**", color=0xdf213)
    buttons = [[]]

    for item in player_inventory:
        buttons[0].append(Button(style=ButtonStyle.gray, label=f"{item} x{player_inventory[item]}"))
    await ctx.channel.send(embed=emb, components=buttons)


# КОМАНДА, открывающая инвентарь
@slash.slash(
    name="open_inventory",
    description="Открыть инвентарь персонажа",
    guild_ids=test_servers_id
)
@commands.has_role("Игрок")
async def open_inventory(ctx):
    value_emoji = client.get_emoji(emoji["money"])
    player = ctx.author
    user = db_sess.query(User).filter(User.id == player.id).first()
    player_inventory = {}
    for item in user.inventory.split(";"):
        player_inventory[item] = player_inventory.get(item, 0) + 1

    emb = discord.Embed(title="**˹ Инвентарь ˼**", color=0xFFFFF0)
    for item in player_inventory:
        price = -1
        emb.add_field(name=f"**{item.upper()}**",
                      value=f"Кол-во: {player_inventory[item]}\nЦена: {price} {value_emoji}",
                      inline=True)

    await ctx.send(embed=emb)


# Обработчик ошибок implement
@implement.error
async def implementation_error(ctx, error):
    await ctx.message.delete()
    if isinstance(error, MissingPermissions):
        await throw_error(ctx, 403)


# Обработчик ошибок reset
@reset.error
async def reset_error(ctx, error):
    await ctx.message.delete()
    if isinstance(error, CommandInvokeError):
        pass
    if isinstance(error, MissingPermissions):
        await throw_error(ctx, 403)


# Обработчик ошибок open_inventory
@open_inventory.error
async def inventory_error(ctx, error):
    if isinstance(error, MissingRole):
        await throw_error(ctx, 404)


# 100 - Выбран неверный пользователь (автор или бот)
# 403 - Нет прав для пользования командой
# 404 - Не найдена роль
async def throw_error(ctx, error_code):
    text = ""
    if error_code == 100:
        text = "Выбран неверный пользователь для действия.\nНельзя выбирать ботов и самого себя!"
    elif error_code == 403:
        text = "У вас недостаточно прав для использования этой команды. (как иронично)"
    elif error_code == 404:
        text = f"У вас нет роли \"Игрок\" для использования этой команды."

    emb = discord.Embed(title="__**БОТ СТОЛКНУЛСЯ С ОШИБКОЙ**__", color=0xed4337)
    emb.add_field(name="**Причина:**",
                  value=f"```diff\n- {text}\n```",
                  inline=False)
    await ctx.send(embed=emb)


# Запуск
DiscordComponents(client)
client.run(TOKEN)
