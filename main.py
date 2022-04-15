import os
import json
import asyncio
import aiohttp
import discord
import datetime

from discord.ext import commands
from discord.ext.commands import MissingPermissions, MissingRole, CommandInvokeError
from discord.utils import get
from discord_slash import SlashCommand
from discord_components import DiscordComponents, Button, ButtonStyle
from discord import FFmpegPCMAudio

from pafy import new

from consts import *
from data import db_session
from data.users import User


"""
====================================================================================================================
====================================== РАЗДЕЛ С ПЕРЕМЕННЫМИ И НАСТРОЙКОЙ БОТА ======================================
====================================================================================================================
"""


# Сервера
test_servers_id = [936293335063232672]
# Переменные (настройка бота)
activity = discord.Activity(type=discord.ActivityType.listening, name="Древнерусский рейв")
intents = discord.Intents.default()
intents.members = True
# Переменные (настройка бота)
client = commands.Bot(command_prefix=PREFIX, intents=intents, activity=activity)
slash = SlashCommand(client, sync_commands=True)
# Подключение к бд
db_session.global_init(f"db/DataBase.db")
db_sess = db_session.create_session()


"""
====================================================================================================================
================================================ РАЗДЕЛ С СОБЫТИЯМИ ================================================
====================================================================================================================
"""


# СОБЫТИЕ, показывающее то что бот запустился
@client.event
async def on_ready():
    # Уведомление
    print("Бот запустился")
    # thrd = ScheduledFunction()
    # thrd.start()
    await store_update_cycle()
    # Подключение к каналу "🎶Главная тема" на всех серверах
    await channel_connection()


# СОБЫТИЕ, обрабатывающее нажатие кнопок
@client.event
async def on_button_click(interaction):
    decision_type = interaction.component.label

    if decision_type == "Принять обмен":
        msg = interaction.message
        embed = msg.embeds[0]
        sender_id, other_id, guild_id = map(int, embed.fields[-1].value.split("\n"))
        guild = client.get_guild(guild_id)
        sender_items = embed.fields[0].value
        other_items = embed.fields[1].value

        if sender_items != "Целое ничего":
            for line in sender_items.split("\n"):
                sender_item = line.split()[0]
                await remove_item(guild, sender_id, sender_item)
                await add_item(guild, other_id, sender_item)
        if other_items != "Целое ничего":
            for line in other_items.split("\n"):
                other_item = line.split()[0]
                await remove_item(guild, other_id, other_item)
                await add_item(guild, sender_id, other_item)

        await guild.get_member(other_id).send("Done!")
        await guild.get_member(sender_id).send("Done!")
        await msg.delete()
        return
    if decision_type == "Отклонить обмен":
        msg = interaction.message
        embed = msg.embeds[0]
        sender_id, other_id, guild_id = map(int, embed.fields[-1].value.split("\n"))
        guild = client.get_guild(guild_id)
        await guild.get_member(sender_id).send(f":x: {guild.get_member(other_id).name} не принял обмен")
        await msg.delete()
        return

    guild = interaction.guild
    member = interaction.user
    id_user = f"{member.id}-{guild.id}"
    if decision_type in group_lbl_button_nation:
        user = db_sess.query(User).filter(User.id == id_user).first()
        user.nation = decision_type
        await interaction.send(f"*Теперь вы пренадлежите расе **{decision_type}**!* [Это сообщение можно удалить]")
        return
    if decision_type in group_lbl_button_origin:
        user = db_sess.query(User).filter(User.id == id_user).first()
        user.origin = decision_type
        await interaction.send(f"*Теперь вы из \"**{decision_type}**\"!* [Это сообщение можно удалить]")
        return

    msg = interaction.message
    embed = msg.embeds[0]
    sender_id, other_id = map(int, embed.fields[-1].value.split("\n")[:-1])
    if member.id != sender_id:
        return

    if decision_type == "Отправить обмен":
        await interaction.send("Обмен отправлен! [Это сообщение можно удалить]")
        await guild.get_member(other_id).send(
            "Вам отправлен обмен! Детали:",
            embed=embed,
            components=[
                [Button(style=ButtonStyle.green, label="Принять обмен"),
                 Button(style=ButtonStyle.red, label="Отклонить обмен")]
            ]
        )
    if decision_type == "Отменить обмен":
        await interaction.send("Обмен отменён [Это сообщение можно удалить]")
        await interaction.message.delete()
    db_sess.commit()


# СОБЫТИЕ, перехватывающее неверную команду
@client.event
async def on_command_error(ctx, error):
    await ctx.message.delete()
    if isinstance(error, commands.CommandNotFound):
        await throw_error(ctx, 105)


"""
====================================================================================================================
=========================== РАЗДЕЛ С КОМАНДАМИ НАСТРАИВАЮЩИМИ СЕРВЕР И ФУНКЦИЯМИ ДЛЯ НИХ ===========================
====================================================================================================================
"""


# ФУНКЦИЯ, подключение к каналу "🎶Главная тема" на всех серверах
async def channel_connection():
    for guild in client.guilds:
        voice_channel = get(guild.voice_channels, name="🎶Главная тема")
        if voice_channel:
            try:
                # Подключение к каналу
                voice = await voice_channel.connect()
                # Включение музыки
                video = new('https://www.youtube.com/watch?v=z_HWtzUHm6s&t=1s')
                audio = video.getbestaudio().url
                voice.play(FFmpegPCMAudio(audio, **ffmpeg_opts, executable="ffmpeg/bin/ffmpeg.exe"))
            except Exception as e:
                print(e)


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
            [Button(style=ButtonStyle.gray, label="Северяне", emoji=client.get_emoji(emoji["north"])),
             Button(style=ButtonStyle.gray, label="Южане", emoji=client.get_emoji(emoji["south"])),
             Button(style=ButtonStyle.gray, label="Техно-гики", emoji=client.get_emoji(emoji["techno"]))]
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
            [Button(style=ButtonStyle.gray, label="Богатая семья", emoji=client.get_emoji(emoji["rich"])),
             Button(style=ButtonStyle.gray, label="Обычная семья", emoji=client.get_emoji(emoji["norm"])),
             Button(style=ButtonStyle.gray, label="Бедность", emoji=client.get_emoji(emoji["poor"]))]
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


# ФУНКЦИЯ, отправляющаю сообщение в чат информации
async def send_information_msg(channel):
    # ======= История
    text = '*```yaml\n' \
           '  Около века назад человечество смогло покинуть Землю и освоить Марс, на нём люди нашли руду под' \
           'названием Экзорий. Люди тщательно изучали Экзорий, и открыли для себя много разных свойств этой руды, в' \
           'результате многих экспериментов люди смогли извлекать из этой руды много энергии с огромной мощью. В ходе' \
           'таких открытий люди смогли быстро развить технологии и освоить космос намного лучше, человечество стало' \
           'путешествовать и колонизировать различные планеты в различных звёздных системах.\n' \
           '  Земля в своё время, к сожалению стала деградировать, из за экспериментов которые проводили на Земле и' \
           'людей отвергающих новые технологии, родная планета человечества через некоторое время стала скверным' \
           'местом. На Землю стали отправлять неугодных людей, которые совершали какие либо преступление. Уже' \
           'несколько поколений люди с планеты Земля живут в ужасном мире этой планеты. Вы родились на Земле, и' \
           'вам предстоит на ней выжить.```*'
    emb = discord.Embed(title='⮮ __**История:**__', color=44444)
    emb.add_field(name='**――**', value=text, inline=False)

    await channel.send(embed=emb)

    # ======= Правила
    text = '*```yaml\n' \
           '➢ -.```*'
    emb = discord.Embed(title='⮮ __**Правила:**__', color=44444)
    emb.add_field(name='**――**', value=text, inline=False)

    await channel.send(embed=emb)


# ФУНКЦИЯ, записывающая всех с сервера в базу данных
async def write_db(guild):
    chek_write_db = False
    for member in guild.members:
        id_user = f"{member.id}-{guild.id}"
        if not member.bot and not db_sess.query(User).filter(User.id == id_user).first():
            user = User()
            user.id = id_user
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
            chek_write_db = True
    db_sess.commit()
    return chek_write_db


# ФУНКЦИЯ, удаляющая всех с сервера из базы данных
async def delete_db(guild):
    for member in guild.members:
        user = db_sess.query(User).filter(User.id == f"{member.id}-{guild.id}").first()
        if not member.bot and user:
            db_sess.delete(user)
    db_sess.commit()


# ФУНКЦИЯ, создающая категории
async def create_category(guild, title):
    return await guild.create_category(title)


# ФУНКЦИЯ, создающая чаты
async def create_channel(guild, channel_info, category, title, roles_for_permss):
    kind, allow_messaging, pos = channel_info
    channel = None
    # Создание чата
    if not get(guild.channels, name=title):
        channel = await guild.create_text_channel(title, category=category, position=pos)
        # Настройка доступа к чату
        if kind != 'all':
            for _name, role in roles_for_permss.items():
                await channel.set_permissions(role, send_messages=allow_messaging, read_messages=kind == _name)
    return channel


# КОМАНДА, настраивающая сервер
@client.command()
@commands.has_guild_permissions(administrator=True)
async def implement(ctx):
    try:
        await ctx.message.delete()
        guild = ctx.guild
        chek_implement = False
        color1 = 44444
        color2 = 16777215
        # Создание ролей
        setting_roles = [("Игрок", color1), ("Тополис", color2), ("Браифаст", color2), ("Джадифф", color2)]
        for _name, color in setting_roles:
            if not get(guild.roles, name=_name):
                await guild.create_role(name=_name, color=color)
                await ctx.send(f":white_check_mark: *Роль {_name} создана.*")
                chek_implement = True

        roles_for_permss = {
            "non-game": guild.default_role,
            "game": get(guild.roles, name="Игрок"),
            "city_topolis": get(guild.roles, name="Тополис"),
            "city_braifast": get(guild.roles, name="Браифаст"),
            "city_jadiff": get(guild.roles, name="Джадифф")
        }

        # Создание чатов и категорий
        for category, channels in Objects.items():
            # Создание категории
            _category = get(guild.categories, name=category)
            if not _category:
                _category = await create_category(guild, category)
                chek_implement = True
                await ctx.send(f":white_check_mark: *Категория {category} создана.*")
            # Создание чатов
            for channel in channels.keys():
                channel = await create_channel(guild, channels[channel].values(), _category, channel, roles_for_permss)
                if channel:
                    chek_implement = True
                    _name = "🚪создание-персонажа"
                    if channel.name == _name:
                        await send_registration_msg(get(guild.channels, name=_name))
                    _name = "📜информация"
                    if channel.name == _name:
                        await send_information_msg(get(guild.channels, name=_name))
                    _name = "🛒магазин"
                    if channel.name == _name:
                        pass
            # Добавление чатов в категорию (сделано для повторного /implement)
            for channel in channels.keys():
                await get(guild.channels, name=channel).edit(category=_category, position=channels[channel]["position"])

        # Создание канала для прослушивания музыки
        name_voice = "🎶Главная тема"
        if not get(guild.voice_channels, name=name_voice):
            channel = await guild.create_voice_channel(name_voice,
                                                       category=get(guild.categories, name="ОБЩЕЕ"), position=4)
            await channel.set_permissions(roles_for_permss["non-game"], speak=False, view_channel=False)
            await channel.set_permissions(roles_for_permss["game"], speak=False, view_channel=True)
            chek_implement = True

        # Заполнение базы данных
        if await write_db(guild):
            await ctx.send(":white_check_mark: *База данных заполнена.*")
            chek_implement = True

        # Подключение к каналу "🎶Главная тема"
        await channel_connection()

        # Уведомление
        if chek_implement:
            await ctx.send(":white_check_mark: **Готово!**")
        else:
            await ctx.send(":x: **Первоначальная настройка уже была произведена!**")
    except Exception as e:
        print(e)
        await ctx.send(":x: **Ой! Что то пошло не так.**")


# КОМАНДА, удаляющая настройку сервера
@client.command()
@commands.has_guild_permissions(administrator=True)
async def reset(ctx):
    await ctx.message.delete()
    guild = ctx.guild
    # Удаление чатов категорий и тд
    discord_objects = []
    for category, channels in Objects.items():
        discord_objects.append(get(guild.categories, name=category))
        for channel in channels.keys():
            discord_objects.append(get(guild.channels, name=channel))
    for role in roles_game:
        discord_objects.append(get(guild.roles, name=role))

    for discord_object in discord_objects:
        if discord_object:
            await discord_object.delete()

    # Удаление канала для музыки
    await get(guild.voice_channels, name="🎶Главная тема").delete()

    # Удаление базы данных
    await delete_db(guild)

    # Уведомление
    await ctx.send(":white_check_mark: **Готово!**")


# КОМАНДА, удаляющая всех с сервера из базы данных
@client.command()
@commands.has_guild_permissions(administrator=True)
async def delete_users(ctx):
    await ctx.message.delete()
    guild = ctx.guild
    chek_delete_db = False
    for member in guild.members:
        user = db_sess.query(User).filter(User.id == f"{member.id}-{guild.id}").first()
        if not member.bot and user:
            db_sess.delete(user)
            chek_delete_db = True
    db_sess.commit()
    # Уведомление
    if chek_delete_db:
        await ctx.send(":white_check_mark: **Готово!**")
    else:
        await ctx.send(":x: **Пользователей нет в базе данных!**")


"""
====================================================================================================================
========================================= РАЗДЕЛ С ФУНКЦИЯМИ ДЛЯ МАГАЗИНА ==========================================
====================================================================================================================
"""


# ФУНКЦИЯ, обновляющая магазин
async def store_update():
    for guild in client.guilds:
        store_channel = get(guild.channels, name="🛒магазин")
        if store_channel:
            # Удаление сообщений
            await store_channel.purge(limit=None)
            # Embed сообщения
            text = '*```yaml\n' \
                   '123.```*'
            emb = discord.Embed(title='⮮ __**МАГАЗИН:**__', color=44444)
            emb.add_field(name='**123:**', value=text, inline=False)
            # Отправка сообщения
            await store_channel.send(
                embed=emb,
                components=[
                    [Button(style=ButtonStyle.gray, label="1"),
                     Button(style=ButtonStyle.gray, label="2"),
                     Button(style=ButtonStyle.gray, label="3")]
                ]
            )


# ФУНКЦИЯ, проверяющая нужно ли обновить магазин
async def store_update_cycle():
    while True:
        if datetime.datetime.now().strftime("%H:%M") == "18:00":
            await store_update()
        await asyncio.sleep(60)


"""
====================================================================================================================
================================== РАЗДЕЛ С КОМАНДАМИ ВЗАИМОДЕЙСТВИЯ С ИНВЕНТАРЁМ ==================================
====================================================================================================================
"""


# КОМАНДА, добавляющая предмет
async def add_item(guild, player_id, item):
    db_sess.query(User).filter(User.id == f"{player_id}-{guild.id}").first().inventory += f";{item}"
    db_sess.commit()


async def remove_item(guild, player_id, item):
    user = db_sess.query(User).filter(User.id == f"{player_id}-{guild.id}").first()
    inventory_list = user.inventory.split(";")
    inventory_list.remove(item)
    user.inventory = ";".join(inventory_list)
    db_sess.commit()


async def get_inventory(player_id, guild):
    user = db_sess.query(User).filter(User.id == f"{player_id}-{guild.id}").first()
    player_inventory = {}
    for item in user.inventory.split(";"):
        player_inventory[item] = player_inventory.get(item, 0) + 1
    return player_inventory


# КОМАНДА, трейд
@slash.slash(
    name="trade",
    description="Отправить предложение обмена другому игроку.",
    options=[{"name": "member", "description": "пользователь", "type": 6, "required": True},
             {"name": "your_items", "description": "Информация о ваших предметах обмена через запятую формата - "
                                                   "ID предмета:Количество", "type": 3, "required": False},
             {"name": "their_items", "description": "Информация о предметах обмена другого человека через запятую "
                                                    "формата - ID предмета:Количество", "type": 3, "required": False}],
    guild_ids=test_servers_id
)
@commands.has_role("Игрок")
async def trade(ctx, member, your_items=None, their_items=None):
    player = ctx.author
    guild = ctx.guild
    if player == member or member.bot or get(guild.roles, name="Игрок") not in member.roles:
        await throw_error(ctx, 100)
        return
    if not your_items and not their_items:
        await throw_error(ctx, 15)

    formatted_player_offer_items = ["Целое ничего"]
    formatted_member_offer_items = ["Целое ничего"]

    if your_items:
        player_inventory = await get_inventory(player.id, guild)
        player_items_list = list(player_inventory.keys())
        formatted_player_offer_items = []
        for player_offer_item_info in your_items.split(","):
            item_id, amount = player_offer_item_info.split(":")
            formatted_player_offer_items.append(f"{player_items_list[int(item_id) - 1]} - x{amount}")
    if their_items:
        member_inventory = await get_inventory(member.id, guild)
        member_items_list = list(member_inventory.keys())
        formatted_member_offer_items = []
        for member_offer_item_info in their_items.split(","):
            item_id, amount = member_offer_item_info.split(":")
            formatted_member_offer_items.append(f"{member_items_list[int(item_id) - 1]} - x{amount}")

    embed = discord.Embed(title="**˹** Предложение обмена сформировано **˼**", color=0xFFFFF0)
    embed.set_author(name=f"Информация: {player.name} → {member.name}")
    embed.add_field(name=f"Предметы {player.name}:", value="\n".join(formatted_player_offer_items))
    embed.add_field(name=f"Предметы {member.name}:", value="\n".join(formatted_member_offer_items))
    embed.add_field(name="_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_",
                    value=f"{player.id}\n{member.id}\n{guild.id}", inline=False)

    msg = await ctx.send("Обмен сформирован!")
    await msg.delete()
    await ctx.channel.send(
        embed=embed,
        components=[
            [Button(style=ButtonStyle.green, label="Отправить обмен"),
             Button(style=ButtonStyle.red, label="Отменить обмен")]
        ]
    )


# КОМАНДА, открывающая инвентарь
@slash.slash(
    name="open_inventory",
    description="Открыть инвентарь персонажа.",
    options=[{"name": "member", "description": "пользователь", "type": 6, "required": False}],
    guild_ids=test_servers_id
)
@commands.has_role("Игрок")
async def open_inventory(ctx, member=None):
    guild = ctx.guild
    if member.bot or get(guild.roles, name="Игрок") not in member.roles:
        await throw_error(ctx, 100)
        return

    value_emoji = client.get_emoji(emoji["money"])
    player = member if not member else ctx.author
    player_inventory = await get_inventory(player.id, guild)
    emb = discord.Embed(title=f"**˹ Инвентарь {player.name}˼**", color=0xFFFFF0)

    item_id = 1
    for item, amount in player_inventory.items():
        price = -1
        emb.add_field(name=f"**{item_id}. {item.upper()}**",
                      value=f"Кол-во: {amount}\nЦена: {price} {value_emoji}",
                      inline=True)
        item_id += 1

    await ctx.send(embed=emb)


"""
====================================================================================================================
===================================== РАЗДЕЛ С ПРОЧИМИ КОМАНДАМИ ДЛЯ ИГРОКОВ =======================================
====================================================================================================================
"""


# КОМАНДА, добавляющая ник и создающая профиль
@client.command()
async def name(ctx, *args):
    await ctx.message.delete()
    guild = ctx.guild
    member = ctx.author

    # Проверка в нужном ли чате используется команда
    name_channel = "🚪создание-персонажа"
    if ctx.channel.id != get(guild.channels, name=name_channel).id:
        await member.send(f":x: **Данную команду вы можете использовать только в чате \"{name_channel}\".**")
        return
    # Проверка на присутствие самого имени
    if not args:
        await member.send(f":x: **Введите имя через пробел после команды, имя не может отсутствовать.**")
        return

    _name = ' '.join(args)
    user = db_sess.query(User).filter(User.id == f"{member.id}-{guild.id}").first()

    for role in member.roles:
        if role.name == 'Игрок':
            await member.send(':x: **Вы не можете поменять своё имя!** *Для этого обратитесь к администрации.*')
            return
    if user.nation == '-1' or user.origin == '-1':
        await member.send(':x: **Вы не можете создать профиль не выбрав расу или происхождение!**')
        return
    await member.send(':white_check_mark: **Вы успешно создали своего персонажа, удачной игры!**')

    user.name = _name
    # Добавляется роль @Игрок
    role = get(guild.roles, name="Игрок")
    await member.add_roles(role)
    # Добавляется роль в зависимости от города
    if user.nation == 'Северяне':
        role = get(guild.roles, name="Тополис")
    elif user.nation == 'Техно-гики':
        role = get(guild.roles, name="Браифаст")
    elif user.nation == 'Южане':
        role = get(guild.roles, name="Джадифф")
    await member.add_roles(role)
    db_sess.commit()


# КОМАНДА, перемещение между городами
@slash.slash(
    name="move",
    description="Отправиться в другой город!",
    options=[{"name": "city", "description": "Роль города в который вы хотите пойти.", "type": 8, "required": True}],
    guild_ids=test_servers_id
)
@commands.has_role("Игрок")
async def move(ctx, city):
    guild = ctx.guild
    author = ctx.author
    user = db_sess.query(User).filter(User.id == f"{author.id}-{guild.id}").first()

    if city.name in ["Тополис", "Браифаст", "Джадифф"]:
        if city in author.roles:
            await ctx.send(':x: **Нельзя выбрать город в котором вы находитесь.**')
            return
        # Удаление роли прошлого города
        await author.remove_roles(get(guild.roles, name="Тополис"))
        await author.remove_roles(get(guild.roles, name="Браифаст"))
        await author.remove_roles(get(guild.roles, name="Джадифф"))
        time_second = 8 * (60 - int(user.speed))
        # Уведомление
        await ctx.send(f"**{author.mention} отправился в город {city.name}.**")
        await author.send(f":white_check_mark: **Время которое затратиться на дорогу: {str(time_second / 60)[0]} "
                          f"минут {time_second % 60} секунд.**")
        # Таймер
        await asyncio.sleep(time_second)
        # Добавление роли нового города
        await author.add_roles(city)
        # Уведомление
        await get(guild.channels, name=f"таверна-{city.name[0].lower()}").send(f"{author.mention} *прибыл!*")
        await author.send(f":white_check_mark: **С прибытием в {city.name}.**")
    else:
        await ctx.send(':x: **Выберите роль обозначающую город.**')


"""
====================================================================================================================
========================================== РАЗДЕЛ С ОБРАБОТЧИКАМИ ОШИБОК ===========================================
====================================================================================================================
"""


# # ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ
# 15 - Отправлен пустой обмен
# 100 - Выбран неверный пользователь (автор или бот)
# 105 - Команда не найдена
# 403 - Нет прав для пользования командой
# 404 - Не найдена роль


# Обработчик ошибок функции move
@move.error
async def move_error(ctx, error):
    if isinstance(error, MissingRole):
        await throw_error(ctx, 404)


# Обработчик ошибок функции trade
@trade.error
async def trade_error(ctx, error):
    if isinstance(error, MissingRole):
        await throw_error(ctx, 404)
    print(error)


# Обработчик ошибок функции implement
@implement.error
async def implementation_error(ctx, error):
    await ctx.message.delete()
    if isinstance(error, MissingPermissions):
        await throw_error(ctx, 403)


# Обработчик ошибок функции reset
@reset.error
async def reset_error(ctx, error):
    await ctx.message.delete()
    if isinstance(error, CommandInvokeError):
        pass
    if isinstance(error, MissingPermissions):
        await throw_error(ctx, 403)


# Обработчик ошибок функции open_inventory
@open_inventory.error
async def inventory_error(ctx, error):
    if isinstance(error, MissingRole):
        await throw_error(ctx, 404)


async def throw_error(ctx, error_code):
    text = ""
    if error_code == 15:
        text = "Не стоит отправлять пустые обмены.\nЕсли у вас нечего отправить другому человеку," \
               " то стоит поиграть немного и заработать немного предметов!"
    elif error_code == 100:
        text = "Выбран неверный пользователь для действия.\nНельзя выбирать ботов и самого себя!"
    elif error_code == 105:
        text = f"Неверная команда! Для получения списка команд достаточно нажать \"{PREFIX}\""
    elif error_code == 403:
        text = "У вас недостаточно прав для использования этой команды. (как иронично)"
    elif error_code == 404:
        text = f"У вас нет роли \"Игрок\" для использования этой команды."

    emb = discord.Embed(title="__**БОТ СТОЛКНУЛСЯ С ОШИБКОЙ**__", color=0xed4337)
    emb.add_field(name="**Причина:**",
                  value=f"```diff\n- {text}\n```",
                  inline=False)
    await ctx.send(embed=emb)


"""
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- ЗАПУСК БОТА -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
"""

DiscordComponents(client)
client.run(TOKEN)
