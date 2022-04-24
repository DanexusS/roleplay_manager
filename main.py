import base64
import asyncio
import discord
import datetime
import random

from discord.ext import commands
from discord.ext.commands import MissingPermissions, MissingRole
from discord.utils import get
from discord_slash import SlashCommand
from discord_components import DiscordComponents, Button, ButtonStyle
from discord import FFmpegPCMAudio

from pafy import new

from discord_exceptions import *
from consts import *
from data import db_session
from data.users import User
from data.items import Items


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


# СОБЫТИЕ, показывающее то, что бот запустился
@client.event
async def on_ready():
    # Уведомление
    print("Бот запустился")
    # Подключение к каналу "🎶Главная тема" на всех серверах
    await channel_connection()
    # Запуск цикла обновления магазина
    await store_update_cycle()


# СОБЫТИЕ, обрабатывающее нажатие кнопок
@client.event
async def on_button_click(interaction):
    decision_type = interaction.component.label

    if decision_type == "Принять обмен":
        msg = interaction.message
        embed = msg.embeds[0]

        footer_text = embed.footer.text.split("\n")[1]
        data = str(base64.b64decode(footer_text))[2:-1]
        sender_id, other_id, guild_id = map(int, data.split(";"))

        guild = client.get_guild(guild_id)
        sender_items = embed.fields[0].value
        other_items = embed.fields[1].value

        if sender_items != "Целое ничего":
            await swap_items(guild, sender_items, sender_id, other_id)
        if other_items != "Целое ничего":
            await swap_items(guild, other_items, sender_id, other_id)

        await guild.get_member(other_id).send("Done!")
        await guild.get_member(sender_id).send("Done!")
        await msg.delete()
        return

    if decision_type == "Отклонить обмен":
        msg = interaction.message
        embed = msg.embeds[0]

        footer_text = embed.footer.text.split("\n")[1]
        data = str(base64.b64decode(footer_text))[2:-1]
        sender_id, other_id, guild_id = map(int, data.split(";"))

        guild = client.get_guild(guild_id)

        await guild.get_member(sender_id).send(f":x: {guild.get_member(other_id).name} не принял обмен")
        await msg.delete()
        return

    guild = interaction.guild
    member = interaction.user
    id_user = f"{member.id}-{guild.id}"

    if "Купить" in decision_type:
        value_emoji = client.get_emoji(emoji['money'])
        item_name = decision_type.split()[1]
        item = db_sess.query(Items).filter(Items.name == item_name).first()
        user = db_sess.query(User).filter(User.id == f"{member.id}-{guild.id}").first()

        if user.money - item.price < 0:
            await interaction.send(f"***Вам не хватило денег**! Ваш баланс: {user.money} {value_emoji}* "
                                   f"[Это сообщение можно удалить]")
        else:
            user.money -= item.price
            await add_item(guild, member.id, item_name)
            await interaction.send(f"*Вы приобрели **{item_name}**! Ваш баланс: {user.money} {value_emoji}* "
                                   f"[Это сообщение можно удалить]")

        db_sess.commit()
        return

    if decision_type in group_lbl_button_nation:
        user = db_sess.query(User).filter(User.id == id_user).first()
        user.nation = decision_type

        await interaction.send(f"*Теперь вы пренадлежите расе **{decision_type}**!* [Это сообщение можно удалить]")
        db_sess.commit()
        return

    if decision_type in group_lbl_button_origin:
        user = db_sess.query(User).filter(User.id == id_user).first()
        user.origin = decision_type

        await interaction.send(f"*Теперь вы из \"**{decision_type}**\"!* [Это сообщение можно удалить]")
        db_sess.commit()
        return

    msg = interaction.message
    embed = msg.embeds[0]
    footer_text = embed.footer.text.split("\n")[1]
    data = str(base64.b64decode(footer_text))[2:-1]
    sender_id, other_id = map(int, data.split(";")[:-1])

    if member.id != sender_id:
        return

    if decision_type == "Отправить обмен":
        await interaction.send("Обмен отправлен! [Это сообщение можно удалить]")
        await interaction.message.delete()

        embed.title = "᲼᲼᲼᲼᲼᲼᲼᲼**˹** Вам было отправлено предложение обмена **˼**"
        await guild.get_member(other_id).send(
            "Вам отправлен обмен! Детали:",
            embed=embed,
            components=[
                [Button(style=ButtonStyle.green, label="Принять обмен"),
                 Button(style=ButtonStyle.red, label="Отклонить обмен")]
            ]
        )
        return

    if decision_type == "Отменить обмен":
        await interaction.send("Обмен отменён [Это сообщение можно удалить]")
        await interaction.message.delete()
        return


@client.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    _message = reaction.message
    _emoji = reaction.emoji

    if _emoji == "✅" and "Чтобы принять участие в партии покера" in _message.content:
        text = _message.content
        members = [await clean_member_id(member.split("  ")[-1]) for member in text.split("\n")[4:]]

        if user.id in members:
            return

        if "Отсутствуют :(" in text:
            text = "\n".join(text.split("\n")[:-1])
            text += f"\n᲼᲼᲼{numbers_emoji[1]}  {user.mention}"
        else:
            number = len(text.split("\n")) - 3
            text += f"\n᲼᲼᲼{numbers_emoji[number]}  {user.mention}"

        await _message.edit(content=text)


# СОБЫТИЕ,
@client.event
async def on_command_error(ctx, error):
    await ctx.message.delete()
    if isinstance(error, commands.CommandNotFound):
        await throw_error(ctx, error)


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
            user.inventory = 'Glock 21;Glock 21;Glock 21;Glock 21'
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
    await ctx.message.delete()
    guild = ctx.guild
    check_implement = False

    # Создание ролей
    for _name, color in roles_game.items():
        if not get(guild.roles, name=_name):
            await guild.create_role(name=_name, color=color)
            await ctx.send(f":white_check_mark: *Роль {_name} создана.*")
            check_implement = True

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
            check_implement = True
            await ctx.send(f":white_check_mark: *Категория {category} создана.*")
        # Создание чатов
        for channel in channels.keys():
            channel = await create_channel(guild, channels[channel].values(), _category, channel, roles_for_permss)
            if channel:
                check_implement = True
                if channel.name == "🚪создание-персонажа":
                    await send_registration_msg(get(guild.channels, name="🚪создание-персонажа"))
                if channel.name == "📜информация":
                    await send_information_msg(get(guild.channels, name="📜информация"))
                if channel.name == "🛒магазин":
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
        check_implement = True

    # Заполнение базы данных
    if await write_db(guild):
        await ctx.send(":white_check_mark: *База данных заполнена.*")
        check_implement = True

    # Создание магазина
    await store_update(guild)

    # Подключение к каналу "🎶Главная тема"
    await channel_connection()

    # Уведомление
    if check_implement:
        await ctx.send(":white_check_mark: **Готово!**")
    else:
        await ctx.send(":x: **Первоначальная настройка уже была произведена!**")


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
async def store_update(guild):
    store_channel = get(guild.channels, name="🛒магазин")
    if store_channel:
        # Удаление сообщений
        await store_channel.purge(limit=None)
        # Список всех предметов
        items_all = db_sess.query(Items).all()
        types = [
            {"NAME": "ОРУЖИЕ",
             "firearms": "Огнестрельное оружие.",
             "steel arms": "Холодное оружие.",
             "energy weapon": "Энергетическое оружие."},
            {"NAME": "ОДЕЖДА",
             "armor": "Одежда, броня."},
            {"NAME": "ЕДА",
             "food": "Еда."}
        ]
        # Магазин
        for _type in types:
            items = list(filter(lambda x: x.type in _type.keys(), items_all.copy()))
            random.shuffle(items)
            items = items[:random.randint(4, 6)]
            # Embed сообщения
            emb = discord.Embed(title=f"⮮ __**{_type['NAME']}:**__", color=0xf1c40f)
            for item in items:
                emb.add_field(
                    name=f"**{item.name}:**",
                    value=f"➢ **Цена:** {item.price} {client.get_emoji(emoji['money'])}"
                          f"```fix\nОписание: {item.description} Тип: {_type[item.type]}```", inline=False
                )
            # Кнопки для покупки
            buttons = [Button(style=ButtonStyle.gray, label=f"Купить {item.name}") for item in items]
            # Отправка сообщения
            await store_channel.send(
                embed=emb,
                components=[buttons]
            )


# ФУНКЦИЯ, проверяющая нужно ли обновить магазин
async def store_update_cycle():
    while True:
        if datetime.datetime.now().strftime("%H:%M") == TIME_STORE_UPDATE:
            for guild in client.guilds:
                await store_update(guild)
        await asyncio.sleep(60)


"""
====================================================================================================================
================================== РАЗДЕЛ С КОМАНДАМИ ВЗАИМОДЕЙСТВИЯ С ИНВЕНТАРЁМ ==================================
====================================================================================================================
"""


# ФУНКЦИЯ, добавляющая предмет в инвентарь
async def add_item(guild, player_id, item):
    db_sess.query(User).filter(User.id == f"{player_id}-{guild.id}").first().inventory += f";{item}"
    db_sess.commit()


# ФУНКЦИЯ, которая убирает предмет из инвентаря
async def remove_item(guild, player_id, item):
    user = db_sess.query(User).filter(User.id == f"{player_id}-{guild.id}").first()
    inventory_list = user.inventory.split(";")
    inventory_list.remove(item)
    user.inventory = ";".join(inventory_list)
    db_sess.commit()


# ФУНКЦИЯ, которая получает инвентарь игрока формата - {предмет:количество}
async def get_inventory(player_id, guild):
    user = db_sess.query(User).filter(User.id == f"{player_id}-{guild.id}").first()
    player_inventory = {}
    for item in user.inventory.split(";"):
        player_inventory[item] = player_inventory.get(item, 0) + 1
    return player_inventory


# ФУНКЦИЯ, которая форматирует предметы для трейда в должный вид
async def get_formatted_items(player_id, guild, items):
    player_inventory = await get_inventory(player_id, guild)
    player_items_list = list(player_inventory.keys())
    formatted_items = []
    for item_info in items.split(","):
        item_id, amount = item_info.split(":")
        formatted_items.append(f"{player_items_list[int(item_id) - 1]} - x{amount}")

    return formatted_items


# ФУНКЦИЯ, которая передаёт предметы из одного инвентаря в другой
async def swap_items(guild, items, sender_id, other_id):
    for line in items.split("\n"):
        item = line.split()[0]
        await remove_item(guild, sender_id, item)
        await add_item(guild, other_id, item)


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
        raise IncorrectUser
    if not your_items and not their_items:
        raise IncompleteTrade

    formatted_player_offer_items = ["Целое ничего"] if not your_items else \
        await get_formatted_items(player.id, guild, your_items)

    formatted_member_offer_items = ["Целое ничего"] if not their_items else \
        await get_formatted_items(member.id, guild, their_items)

    embed = discord.Embed(title="᲼᲼᲼᲼᲼᲼᲼᲼**˹** Предложение обмена сформировано **˼**", color=0xFFFFF0)
    encoded_data = base64.b64encode(f"{player.id};{member.id};{guild.id}".encode("UTF-8"))
    extra_info = str(encoded_data)[2:-1]

    embed.add_field(name=f"Предметы\t{player.name}:", value="\n".join(formatted_player_offer_items))
    embed.add_field(name=f"Предметы\t{member.name}:", value="\n".join(formatted_member_offer_items))
    embed.set_footer(text=f"┈━━━┈━━━┈━━━┈━━━┈━━━┈━━━┈━━━┈━━━┈━━━┈━━━┈\n{extra_info}")

    msg = await ctx.send("Обмен сформирован!")
    await msg.delete()
    await ctx.channel.send(
        embed=embed,
        components=[
            [Button(style=ButtonStyle.green, label="Отправить обмен"),
             Button(style=ButtonStyle.red, label="Отменить обмен")]
        ]
    )


# КОМАНДА, перевод денег
@slash.slash(
    name="money_transfer",
    description="Отправить деньги другому игроку.",
    options=[{"name": "member", "description": "пользователь", "type": 6, "required": True},
             {"name": "amount", "description": "Количество денег для отправки", "type": 4, "required": True}],
    guild_ids=test_servers_id
)
@commands.has_role("Игрок")
async def money_transfer(ctx, member, amount):
    guild = ctx.guild
    if member and (member.bot or get(guild.roles, name="Игрок") not in member.roles):
        raise IncorrectUser

    player = ctx.author
    player_user = db_sess.query(User).filter(User.id == f"{player.id}-{guild.id}").first()
    member_user = db_sess.query(User).filter(User.id == f"{member.id}-{guild.id}").first()

    player_user.money -= amount
    member_user.money += amount

    await ctx.send("Обмен состоялся!")
    db_sess.commit()


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
    if member and (member.bot or get(guild.roles, name="Игрок") not in member.roles):
        raise IncorrectUser

    value_emoji = client.get_emoji(emoji["money"])
    player = member if member else ctx.author
    player_inventory = await get_inventory(player.id, guild)
    emb = discord.Embed(title=f"**˹ Инвентарь {player.name}˼**", color=0xFFFFF0)

    item_id = 1
    for item, amount in player_inventory.items():
        item_obj = db_sess.query(Items).filter(Items.name == item).first()
        text = f"**Порядковый ID: {item_id}**\n" \
               f"Кол-во: {amount}\n" \
               f"Цена: {item_obj.price} {value_emoji}\n" \
               f"Описание: {item_obj.description}"

        emb.add_field(name=f"**__{item.upper()}__**",
                      value=text,
                      inline=True)
        item_id += 1

    balance = db_sess.query(User).filter(User.id == f"{player.id}-{guild.id}").first().money
    emb.set_footer(text=f"Баланс: {balance} Gaudium")

    await ctx.send(embed=emb)


# КОМАНДА, !!! добавляющая предмет в базу данных, нужная только для проектирования бота !!!
@slash.slash(
    name="add_item_db",
    description="Добавить предмет в базу данных.",
    options=[{"name": "_name", "description": "Имя предмета.", "type": 3, "required": True},
             {"name": "_description", "description": "Описание предмета.", "type": 3, "required": True},
             {"name": "_type", "description": "Тип предмета.", "type": 3, "required": True},
             {"name": "_const", "description": "Характеристика предмета.", "type": 3, "required": True},
             {"name": "_price", "description": "Стоимость предмета.", "type": 3, "required": True}],
    guild_ids=test_servers_id
)
async def add_item_db(ctx, _name, _description, _type, _const, _price):
    print(_name, _description, _type, _const, _price)
    # Создание нового предмета
    new_item = Items()
    new_item.name = str(_name)
    new_item.description = str(_description)
    new_item.type = str(_type)
    new_item.const = int(_const)
    new_item.price = int(_price)
    db_sess.add(new_item)
    db_sess.commit()
    # Уведомление
    await ctx.send(":white_check_mark: **Предмет добавлен!**")
# Отключать команду когда она не нужна!


"""
====================================================================================================================
=============================================== РАЗДЕЛ С МИНИ-ИГРАМИ ===============================================
====================================================================================================================
"""


"""
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- КРЕСТИКИ-НОЛИКИ -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
"""


@slash.slash(
    name="tic_tac_toe",
    description="Сыграть в \"Крестики-нолики\"",
    guild_ids=test_servers_id
)
async def tic_tac_toe(ctx):
    pass


"""
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- КАМЕНЬ - НОЖНИЦЫ - БУМАГА -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
"""


@slash.slash(
    name="rock_paper_scissors",
    description="Сыграть в \"Камень-ножницы-бумага\"",
    guild_ids=test_servers_id
)
async def tic_tac_toe(ctx):
    pass


"""
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- ПОКЕР -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
"""


@slash.slash(
    name="poker_help",
    description="Информация о правилах игры покер и о взаимодействии с ботом.",
    guild_ids=test_servers_id
)
async def poker_help(ctx):
    pass


@slash.slash(
    name="start_poker_session",
    description="Начать игру в покер",
    options=[{"name": "members", "description": "Игроки, участвующие в игре. Совет! Просто упомените всех "
                                                "игроков в покер (от 2 до 10 человек)", "type": 3, "required": True},
             {"name": "bet", "description": "Минимально возможная ставка за один ход", "type": 4, "required": True}],
    guild_ids=test_servers_id
)
async def start_poker_session(ctx, members, bet):
    guild = ctx.guild
    raw_member_data = members.split("><") + [ctx.author.id]
    if not 2 <= len(raw_member_data) <= 10:
        raise IncorrectMemberAmount

    members = [guild.get_member(await clean_member_id(member_id)) for member_id in raw_member_data]
    for member in members:
        if member.bot or get(guild.roles, name="Игрок") not in member.roles:
            raise IncorrectUser

    channel_name = f"poker-lobby-{''.join(filter(str.isalnum, ctx.author.name))}".lower()
    channel = get(guild.channels, name=channel_name)
    if channel:
        await channel.delete()

    channel = await guild.create_text_channel(channel_name, category=ctx.channel.category)

    await channel.set_permissions(guild.default_role, send_messages=False, read_messages=False)
    for member in members:
        await channel.set_permissions(member, send_messages=True, read_messages=True)

    members_mentions = [member.mention for member in members]
    members_list = "\n".join(members_mentions)
    await ctx.send(f"Лобби {channel.mention} создано.\n"
                   f"{members_list}")
    msg = await channel.send(f"**ЖДЁМ НАЧАЛА ИГРЫ!**\n"
                             f"Чтобы принять участие в партии покера, нажмите кнопку ✅\n"
                             f"*NB! Для приятной игры, нужно иметь, "
                             f"минимум {round(bet * 1.5)} {client.get_emoji(emoji['money'])}*\n"
                             f"**__Текущие участники:__**\n"
                             f"᲼᲼᲼Отсутствуют :(")
    await msg.add_reaction("✅")
    await msg.pin()


@client.command()
async def play(ctx):
    pins = await ctx.channel.pins()
    message = pins[0].content
    members = [await clean_member_id(member.split("  ")[-1]) for member in message.split("\n")[4:]]

    print(members)


@client.command()
async def call(ctx):
    pass


@client.command()
async def fold(ctx):
    pass


@client.command()
async def reraise(ctx):
    pass


@client.command()
async def check(ctx):
    pass


@client.command(name="raise")
async def _raise(ctx):
    pass


@client.command()
async def leave(ctx):
    member = ctx.author
    channel = ctx.channel

    await channel.set_permissions(member, send_messages=False, read_messages=False)


"""
====================================================================================================================
===================================== РАЗДЕЛ С ПРОЧИМИ КОМАНДАМИ ДЛЯ ИГРОКОВ =======================================
====================================================================================================================
"""


async def clean_member_id(member_id):
    try:
        return int(str(member_id).replace("<", "").replace(">", "").replace("!", "").replace("@", ""))
    except ValueError:
        return ""


# КОМАНДА, для проверки связи :)
@slash.slash(
    name="ping",
    description="Проверка связи!",
    guild_ids=test_servers_id
)
async def ping(ctx):
    await ctx.send('Pong!')


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


@start_poker_session.error
async def start_poker_session_error(ctx, error):
    await throw_error(ctx, error)


# Обработчик ошибок функции move
@move.error
async def move_error(ctx, error):
    await throw_error(ctx, error)


# Обработчик ошибок функции trade
@trade.error
async def trade_error(ctx, error):
    await throw_error(ctx, error)


# Обработчик ошибок функции implement
@implement.error
async def implementation_error(ctx, error):
    await ctx.message.delete()
    await throw_error(ctx, error)


# Обработчик ошибок функции reset
@reset.error
async def reset_error(ctx, error):
    await ctx.message.delete()
    await throw_error(ctx, error)


# Обработчик ошибок функции open_inventory
@open_inventory.error
async def inventory_error(ctx, error):
    await throw_error(ctx, error)


async def throw_error(ctx, error):
    text = error

    if isinstance(error, IncorrectTradeValues):
        text = "- Неверно заданы параметры для трейда. \n NB! Формат предметов выглядит так:" \
               " ID_предмета1:количество_предмета1,ID_предмета2:количество_предмета2"
    if isinstance(error, IncompleteTrade):
        text = "- Не стоит отправлять пустые обмены.\n NB! Если у вас нечего отправить другому человеку, " \
               "то стоит поиграть немного и получить немного предметов!"
    if isinstance(error, IncorrectUser):
        text = "- Выбран неверный пользователь для действия.\n" \
               "NB! Нельзя выбирать ботов, самого себя и пользователей без роли \"Игрок\"!"
    if isinstance(error, MissingRole):
        text = f"- У вас нет роли \"Игрок\" для использования этой команды."
    if isinstance(error, MissingPermissions):
        text = "- У вас недостаточно прав для использования этой команды. (Как иронично)"
    if isinstance(error, commands.CommandNotFound):
        text = "- Неверная команда! Для получения списка команд достаточно нажать \"/\""

    emb = discord.Embed(title="__**БОТ СТОЛКНУЛСЯ С ОШИБКОЙ**__", color=0xed4337)
    emb.add_field(name="**Причина:**",
                  value=f"```diff\n{text}\n```",
                  inline=False)
    await ctx.send(embed=emb)


"""
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- ЗАПУСК БОТА -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
"""

DiscordComponents(client)
client.run(TOKEN)
