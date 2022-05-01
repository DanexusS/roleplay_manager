import base64
import asyncio
import discord
import datetime
import random

from discord import FFmpegPCMAudio
from discord.ext import commands
from discord.ext.commands import MissingPermissions, MissingRole, CommandNotFound
from discord.utils import get
from discord_slash import SlashCommand
from discord_components import DiscordComponents, Button, ButtonStyle

from pafy import new

from extras import *
from consts import *
from data import db_session
from data.users import User
from data.items import Items

"""
====================================================================================================================
====================================== РАЗДЕЛ С ПЕРЕМЕННЫМИ И НАСТРОЙКОЙ БОТА ======================================
====================================================================================================================
"""

# Сервера (нужны для быстрой настройки слэш-комманд
test_servers_id = [936293335063232672]

# Переменные (настройка бота)
activity = discord.Activity(type=discord.ActivityType.listening, name="Древнерусский рейв")
intents = discord.Intents.default()
intents.members = True

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
    # Уведомление об удачном запуске бота
    print("Бот запустился")

    # Подключение к каналу "🎶Главная тема" на всех серверах
    await channel_connection()

    # Запуск цикла обновления магазина
    await store_update_cycle()


# СОБЫТИЕ, обрабатывающее нажатие кнопок
@client.event
async def on_button_click(interaction):
    decision_type = interaction.component.label
    message = interaction.message
    embed = message.embeds[0]

    guild = interaction.guild
    member = interaction.user

    if "Начать раздачу" in decision_type:
        dealer_line = embed.fields[3].value.split("\n")[1]
        dealer_name, dealer_desc = " ".join(dealer_line.split()[1:]).split("#")
        dealer = get(guild.members, name=dealer_name, discriminator=dealer_desc)

        if member.id != dealer.id:
            return

        active_card_decks = json.load(open("game_data/active_card_decks.json", encoding="utf8"))
        active_players_ids = json.load(open("game_data/active_players_ids.json", encoding="utf8"))
        active_player_decks = json.load(open("game_data/active_player_decks.json", encoding="utf8"))

        deck = DeckOfCards()
        await deck.shuffle()
        active_card_decks[str(message.id)] = deck.cards

        active_players = active_players_ids[str(message.id)]

        for player in active_players:
            active_player_decks[str(message.id)][str(player)] = await deck.take(2)

        player_id = 4 if 3 < len(active_players) else 4 % len(active_players)
        old_field_value = "\n".join(embed.fields[3].value.split("\n")[:4])
        embed.set_field_at(3, name="\u200b",
                           value=f"{old_field_value}\n"
                                 f"{player_id + 1}.\t{guild.get_member(active_players[player_id])}\n"
                                 f"Ход раунда: 1 из {len(active_players)}",
                           inline=True)

        await interaction.send("Раздача завершена!")
        await message.edit(embed=embed,
                           components=[Button(style=ButtonStyle.gray, label="Посмотреть свои карты")])

        await commit_changes(active_card_decks, "game_data/active_card_decks.json")
        await commit_changes(active_player_decks, "game_data/active_player_decks.json")

        return

    if "Посмотреть свои карты" in decision_type:
        active_player_decks = json.load(open("game_data/active_player_decks.json", encoding="utf8"))
        await interaction.send(active_player_decks[str(message.id)][str(member.id)])
        return

    if "Купить" in decision_type:
        value_emoji = client.get_emoji(emoji['money'])
        item_name = ' '.join(decision_type.split()[1:])
        item = db_sess.query(Items).filter(Items.name == item_name).first()
        user = db_sess.query(User).filter(User.id == f"{member.id}-{guild.id}").first()

        if user.balance < item.price:
            await interaction.send(f"***Вам не хватило денег**! Ваш баланс: {user.balance} {value_emoji}* "
                                   f"[Это сообщение можно удалить]")
        else:
            user.balance -= item.price
            await add_item(guild, member.id, item_name)
            await interaction.send(f"*Вы приобрели **{item_name}**! Ваш баланс: {user.balance} {value_emoji}* "
                                   f"[Это сообщение можно удалить]")

        db_sess.commit()
        return

    if decision_type in group_lbl_button_nation:
        id_user = f"{member.id}-{guild.id}"
        user = db_sess.query(User).filter(User.id == id_user).first()
        user.nation = decision_type

        await interaction.send(f"*Теперь вы пренадлежите расе **{decision_type}**!* [Это сообщение можно удалить]")
        db_sess.commit()
        return

    if decision_type in group_lbl_button_origin:
        id_user = f"{member.id}-{guild.id}"
        user = db_sess.query(User).filter(User.id == id_user).first()
        user.origin = decision_type

        await interaction.send(f"*Теперь вы из \"**{decision_type}**\"!* [Это сообщение можно удалить]")
        db_sess.commit()
        return

    footer_text = embed.footer.text.split("\n")[1]
    data = str(base64.b64decode(footer_text))[2:-1]
    guild = client.get_guild(int(data))

    sender_name, sender_desc = " ".join(embed.fields[0].name.split()[1:])[:-1].split("#")
    sender = get(guild.members, name=sender_name, discriminator=sender_desc)

    other_name, other_desc = " ".join(embed.fields[1].name.split()[1:])[:-1].split("#")
    other = get(guild.members, name=other_name, discriminator=other_desc)

    if decision_type == "Принять обмен":
        sender_items = embed.fields[0].value
        other_items = embed.fields[1].value

        if sender_items != "Целое ничего":
            await swap_items(guild, sender_items, sender.id, other.id)
        if other_items != "Целое ничего":
            await swap_items(guild, other_items, sender.id, other.id)

        await sender.send("Done!")
        await other.send("Done!")

        channel = await other.create_dm()
        msg = await channel.fetch_message(message.id)
        await msg.delete()
        return

    if decision_type == "Отклонить обмен":
        await sender.send(f":x: {other.name} не принял обмен")
        await message.delete()
        return

    if member.id != sender.id:
        return

    if decision_type == "Отправить обмен":
        await interaction.send("Обмен отправлен! [Это сообщение можно удалить]")
        await message.delete()

        embed.title = "᲼᲼᲼᲼᲼᲼᲼᲼**˹** Вам было отправлено предложение обмена **˼**"
        await other.send(
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
        await message.delete()
        return


@client.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    _message = reaction.message
    _emoji = reaction.emoji
    _channel = _message.channel

    if _emoji == "✅":
        if "Чтобы принять участие в партии покера" in _message.content:
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
        elif "КРЕСТИКИ-НОЛИКИ" in _message.content:
            txt = _message.content.split()
            if txt[2][:-1] == user.name:
                await _message.delete()
                await first_send_tic_tac_toe(_channel, txt[2][:-1], txt[5])

    if _emoji in [numbers_emoji[i] for i in range(1, 10)]:
        emb = _message.embeds[0]
        if emb.fields[0].value.split()[1][:-1] == user.name:
            # num = 0
            # for i in range(1, 10):
            #     if numbers_emoji[i] == _emoji:
            #         num = i
            #         break
            #
            # p1 = emb.fields[0].value.split()[1][:-1]
            # p2, p3 = emb.footer.text.split()[1][:-1], emb.footer.text.split()[3]
            # player = p2 if p1 == p2 else p3
            #
            # cross_and_zero = []
            # count = 1
            # for elem in emb.fields[1].value:
            #     if elem in ['❌', '⭕']:
            #         if count == num:
            #             if player == p2:
            #                 elem = '❌'
            #         cross_and_zero.append(elem)
            #         count += 1
            # print(cross_and_zero)
            #
            # emb.fields[0].value = f"*Ходит: {p2 if player != p2 else p3}*"
            #
            # await msg.edit(embed=emb)

            for _user in await reaction.users().flatten():
                await reaction.remove(_user)


# # СОБЫТИЕ,
# @client.event
# async def on_command_error(ctx, error):
#     print(error)
#     if isinstance(error, CommandNotFound):
#         await ctx.message.delete()
#         await throw_error(ctx, error)


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
           '➢ Имя не влияет на характеристики, при написании команды напишите имя маленькими буквами.\n' \
           '➢ Вводите имя с умом так как его можно будет изменить только через админа.' \
           '➢ После написания имени вы завершите создание профиля.```*'
    emb = discord.Embed(title='⮮ __**Ваше имя:**__', color=44444)
    emb.add_field(name='**Важно:**', value=text, inline=False)

    await channel.send(embed=emb)


# ФУНКЦИЯ, отправляющаю сообщение в чат информации
async def send_information_msg(channel):
    # ======= История
    text = '*```yaml\n' \
           '  Около века назад человечество смогло покинуть Землю и освоить Марс, на нём люди нашли руду под ' \
           'названием Экзорий. Люди тщательно изучали Экзорий, и открыли для себя много разных свойств этой руды, в ' \
           'результате многих экспериментов люди смогли извлекать из этой руды много энергии с огромной мощью. В ходе' \
           ' таких открытий люди смогли быстро развить технологии и освоить космос намного лучше, человечество стало' \
           'путешествовать и колонизировать различные планеты в различных звёздных системах.\n' \
           '  Земля в своё время, к сожалению стала деградировать, из за экспериментов которые проводили на Земле и ' \
           'людей отвергающих новые технологии, родная планета человечества через некоторое время стала скверным ' \
           'местом. На Землю стали отправлять неугодных людей, которые совершали какие либо преступление. Уже ' \
           'несколько поколений люди с планеты Земля живут в ужасном мире этой планеты. Вы родились на Земле, и ' \
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
             "firearms_auto": "Автоматическое огнестрельное оружие.",
             "steel arms": "Холодное оружие.",
             "energy weapon": "Энергетическое оружие."},
            {"NAME": "ОДЕЖДА",
             "armor_head": "Головные уборы.",
             "armor_body": "Верхняя одежда.",
             "armor_legs": "Поножи.",
             "armor_feet": "Обувь."},
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
    user = db_sess.query(User).filter(User.id == f"{player_id}-{guild.id}").first()
    user.inventory += f"{';' if user.inventory != '' else ''}{item}"
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
    user_inventory = db_sess.query(User).filter(User.id == f"{player_id}-{guild.id}").first().inventory
    player_inventory = {}
    if len(user_inventory) != 0:
        for item in user_inventory.split(";"):
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
        item, amount = line.split(" - ")
        for _ in range(int(amount[-1])):
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
    if player == member:
        raise IncorrectUser("- Совершать обмены с самим собой невозможно!\n"
                            "Если вам не с кем обмениваться, то стоит поискать друзей?")
    if member.bot:
        raise IncorrectUser("- Нельзя обмениваться с Ботами!")
    if get(guild.roles, name="Игрок") not in member.roles:
        raise IncorrectUser(f"- У {member.name} нет роли \"Игрок\"!")

    if not your_items and not their_items:
        raise IncompleteTrade(f"- Вы не закончили трейд!\n"
                              f"Если Вы ничего не добавили в обмен, "
                              f"то зачем Вам обмениваться с {member.name} вообще?")

    formatted_player_offer_items = ["Целое ничего"] if not your_items else \
        await get_formatted_items(player.id, guild, your_items)

    formatted_member_offer_items = ["Целое ничего"] if not their_items else \
        await get_formatted_items(member.id, guild, their_items)

    embed = discord.Embed(title="᲼᲼᲼᲼᲼᲼᲼᲼**˹** Предложение обмена сформировано **˼**", color=0xFFFFF0)
    extra_info = str(base64.b64encode(str(guild.id).encode("UTF-8")))[2:-1]

    embed.add_field(name=f"Предметы\t{player}:", value="\n".join(formatted_player_offer_items))
    embed.add_field(name=f"Предметы\t{member}:", value="\n".join(formatted_member_offer_items))
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
    if member.bot:
        raise IncorrectUser("- Ботам передавать деньги нельзя!\n"
                            "(Я бы в принципе не доверял им, кроме меня, конечно, я лучший бот, почти человек!)")
    if get(guild.roles, name="Игрок") not in member.roles:
        raise IncorrectUser(f"- У {member.name} нет роли \"Игрок\"!")

    player = ctx.author
    player_user = db_sess.query(User).filter(User.id == f"{player.id}-{guild.id}").first()
    member_user = db_sess.query(User).filter(User.id == f"{member.id}-{guild.id}").first()

    if amount < 1:
        raise IncorrectMemberAmount(f"- Минимальная сумма перевода = 1!")
    if player_user.balance < amount:
        raise IncorrectMemberAmount(f"- У {player_user.name} нет столько денег!")

    player_user.balance -= amount
    member_user.balance += amount

    await ctx.send(":white_check_mark: **Обмен состоялся!**")
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
    if member:
        if member.bot:
            raise IncorrectUser("- У ботов нет инвентаря!\n"
                                "Даже не пытайтесь открыть у них инвентарь - это бесполезно!")
        if get(guild.roles, name="Игрок") not in member.roles:
            raise IncorrectUser(f"- У {member.name} нет роли \"Игрок\"!")

    value_emoji = client.get_emoji(emoji["money"])
    player = member if member else ctx.author
    player_inventory = await get_inventory(player.id, guild)
    player_name = db_sess.query(User).filter(User.id == f"{player.id}-{guild.id}").first().name
    embed = discord.Embed(title=f"**˹ Инвентарь {player_name}˼**", color=0xFFFFF0)

    if len(player_inventory.keys()) != 0:
        item_id = 1
        for item, amount in player_inventory.items():
            item_obj = db_sess.query(Items).filter(Items.name == item).first()
            text = f"**Порядковый ID:** *{item_id}*\n" \
                   f"**Количество:** *{amount}*\n" \
                   f"**Цена:** *{item_obj.price} {value_emoji}*\n" \
                   f"**Описание:** *{item_obj.description}*"

            embed.add_field(name=f"**__{item.upper()}__**",
                            value=text,
                            inline=True)
            item_id += 1
    else:
        embed.add_field(name="Полностью пуст", value="\u200b")

    balance = db_sess.query(User).filter(User.id == f"{player.id}-{guild.id}").first().balance
    embed.set_footer(text=f"Баланс: {balance} Gaudium")

    await ctx.send(embed=embed)


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
    description="Сыграть в \"Крестики-нолики\".",
    options=[{"name": "member", "description": "Игрок, которого вы вызываете на бой.", "type": 6, "required": True}],
    guild_ids=test_servers_id
)
@commands.has_role("Игрок")
async def send_invite_tic_tac_toe(ctx, member):
    if member.bot:
        raise IncorrectUser("- С ботом играть нельзя!")
    msg = await ctx.send(f"**КРЕСТИКИ-НОЛИКИ**\n*| {member.name}! Вас приглашает {ctx.author.name} "
                         f"сыграть в крестики-нолики!* __*Для подтверждения нажмите на ✅.*__\n"
                         f"||{member.mention}{ctx.author.mention}||")
    await msg.add_reaction("✅")


async def first_send_tic_tac_toe(channel, members1, members2):
    # Рандомный выбор того кто будет за "крестики"
    cross_and_zero = [members1, members2]
    random.shuffle(cross_and_zero)
    # Сообщение-поле игры   |   (❌ or ⭕ | emb.set_footer(text=f""))
    emb = discord.Embed(title=f"**<<= КРЕСТИКИ-НОЛИКИ =>>**", color=44444)
    emb.add_field(name="**. ━━━━━━━━━━━━━━ .**", value=f"*Ходит: {cross_and_zero[0]}*", inline=False)
    text = f"**▫〰{'🔲'}〰 | 〰{'🔲'}〰 | 〰{'🔲'}〰▫**\n" \
           f"**. ━━━━━━━━━━━━━━ .**\n" \
           f"**▫〰{'🔲'}〰 | 〰{'🔲'}〰 | 〰{'🔲'}〰▫**\n" \
           f"**. ━━━━━━━━━━━━━━ .**\n" \
           f"**▫〰{'🔲'}〰 | 〰{'🔲'}〰 | 〰{'🔲'}〰▫**\n" \
           f"**. ━━━━━━━━━━━━━━ .**"
    emb.add_field(name="**. ━━━━━━━━━━━━━━ .**", value=text, inline=False)
    emb.set_footer(text=f"Крестики: {cross_and_zero[0]}; Нолики: {cross_and_zero[1]}")

    msg = await channel.send(embed=emb)

    for i in range(1, 10):
        await msg.add_reaction(numbers_emoji[i])


"""
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- КАМЕНЬ - НОЖНИЦЫ - БУМАГА -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
"""


@slash.slash(
    name="rock_paper_scissors",
    description="Сыграть в \"Камень-ножницы-бумага\".",
    guild_ids=test_servers_id
)
@commands.has_role("Игрок")
async def rock_paper_scissors(ctx):
    pass


"""
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- ПОКЕР -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
"""


@slash.slash(
    name="poker_help",
    description="Информация о правилах игры покер и о взаимодействии с ботом.",
    guild_ids=test_servers_id
)
@commands.has_role("Игрок")
async def poker_help(ctx):
    pass


@slash.slash(
    name="start_poker_session",
    description="Начать игру в покер.",
    options=[{"name": "members", "description": "Игроки, участвующие в игре. Совет! Просто упомените всех "
                                                "игроков в покер (от 2 до 5 человек)", "type": 3, "required": True},
             {"name": "bet", "description": "Плата за вход в игру и размер "
                                            "обязательной ставки (минимум - 10)", "type": 4, "required": True}],
    guild_ids=test_servers_id
)
@commands.has_role("Игрок")
async def start_poker_session(ctx, members, bet):
    guild = ctx.guild
    raw_member_data = members.split("><") + [ctx.author.id]
    if not 2 <= len(raw_member_data) <= 5:
        raise IncorrectMemberAmount(f"- Неверное количество игроков!\n"
                                    f"Для игры в покер нужно от 2 до 5 человек. У вас - {len(raw_member_data)}.")

    members = [guild.get_member(await clean_member_id(member_id)) for member_id in raw_member_data]
    for member in members:
        if member.bot:
            raise IncorrectUser(f"- Выбран неверный пользователь.\n{member.name} - бот!")
        if get(guild.roles, name="Игрок") not in member.roles:
            raise IncorrectUser(f"- Выбран неверный пользователь.\nУ {member.name} нет роли \"Игрок\"!")

    channel_name = f"poker-lobby-{''.join(filter(str.isalnum, ctx.author.name))}".lower()
    channel = get(guild.channels, name=channel_name)
    if channel:
        await channel.delete()

    channel = await guild.create_text_channel(channel_name, category=ctx.channel.category)

    await channel.set_permissions(guild.default_role, send_messages=False, read_messages=False)
    for member in members:
        await channel.set_permissions(member, send_messages=True, read_messages=True)

    games_history = json.load(open("game_data/games_history.json"))
    print(games_history)
    games_history[str(channel.id)] = 0

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

    await commit_changes(games_history, "game_data/games_history.json")


@client.command()
@commands.has_role("Игрок")
async def play(ctx):
    guild = ctx.guild
    channel = ctx.channel
    pins = await channel.pins()
    message_text = pins[-1].content

    games_history = json.load(open("game_data/games_history.json"))

    bet = int(message_text.split("\n")[2].split()[7]) // 1.5
    members_ids = [await clean_member_id(member.split("  ")[-1]) for member in message_text.split("\n")[4:]] * 2
    members = [guild.get_member(member_id) for member_id in members_ids]
    value_emoji = client.get_emoji(emoji["money"])

    games_count = games_history[str(channel.id)]
    dealer_id = games_count if games_count < len(members) else games_count % len(members)
    dealer = members[dealer_id]

    small_blind_id = dealer_id + 1 if dealer_id + 1 < len(members) else (dealer_id + 1) % len(members)
    blind_id = dealer_id + 2 if dealer_id + 2 < len(members) else (dealer_id + 2) % len(members)

    db_sess.query(User).filter(User.id == f"{members_ids[small_blind_id]}-{guild.id}").first().balance -= bet // 2
    db_sess.query(User).filter(User.id == f"{members_ids[blind_id]}-{guild.id}").first().balance -= bet

    embed = discord.Embed(title=f"Партия в покер в процессе", color=0x99d98c)

    members_text = [[], []]
    member_pos = 1
    column = 0
    for member in members:
        balance = db_sess.query(User).filter(User.id == f"{member.id}-{guild.id}").first().balance
        members_text[column].append(f"**{member_pos}.\t{member.name}:**\n"
                                    f"Баланс:\t{balance} {value_emoji}")
        if member_pos == len(members) % 2 + len(members) // 2:
            column += 1
        member_pos += 1

    embed.add_field(name="\u200b", value="\n\n".join(members_text[0]), inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    embed.add_field(name="\u200b", value="\n\n".join(members_text[1]), inline=True)

    embed.add_field(name="\u200b",
                    value=f"**Дилер:**\n"
                          f"{dealer_id + 1}.\t{dealer}\n\n"
                          f"**Сейчас ходит:**\n"
                          f"Никто не ходит.\n"
                          f"(Ожидание раздачи карт)",
                    inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    embed.add_field(name="\u200b",
                    value=f"**Общий куш:**\n"
                          f"{round(1.5 * bet)} {value_emoji}\n\n"
                          f"**Минимальная ставка:**\n"
                          f"{round(bet)} {value_emoji}",
                    inline=True)

    embed.add_field(name="\u200b", value="**Открытые карты:**\n"
                                         "Отсутствуют", inline=True)
    embed.add_field(name="\u200b", value="**Последнее действие:**\n"
                                         "Пока отсутсвует.\n"
                                         "(Ожидание ставок после раздачи)", inline=True)

    # await pins[0].unpin()
    message = await ctx.send(embed=embed,
                             components=[Button(style=ButtonStyle.green, label="Начать раздачу")])
    await message.pin()

    active_players_ids = json.load(open("game_data/active_players_ids.json", encoding="utf8"))
    active_player_decks = json.load(open("game_data/active_player_decks.json", encoding="utf8"))

    games_history[str(channel.id)] += 1

    active_players_ids[str(message.id)] = members_ids
    active_player_decks[str(message.id)] = {}

    await commit_changes(games_history, "game_data/games_history.json")
    await commit_changes(active_players_ids, "game_data/active_players_ids.json")
    await commit_changes(active_player_decks, "game_data/active_player_decks.json")
    db_sess.commit()


@client.command(name="bet")
@commands.has_role("Игрок")
async def _bet(ctx, bet_amount):
    current_player = await get_current_player(ctx)
    if current_player.id != ctx.authur.id:
        raise IncorrectUser("- Сейчас не Ваша очередь ходить!")

    pot, minimal_bet = await get_current_game_info(ctx)
    if minimal_bet > bet_amount:
        bet_amount = minimal_bet


@client.command()
@commands.has_role("Игрок")
async def all_in(ctx):
    current_player = await get_current_player(ctx)
    if current_player.id != ctx.authur.id:
        raise IncorrectUser("- Сейчас не Ваша очередь ходить!")


@client.command()
@commands.has_role("Игрок")
async def call(ctx):
    current_player = await get_current_player(ctx)
    if current_player.id != ctx.authur.id:
        raise IncorrectUser("- Сейчас не Ваша очередь ходить!")

    current_game_info = await get_current_game_info(ctx)


@client.command()
@commands.has_role("Игрок")
async def fold(ctx):
    current_player = await get_current_player(ctx)
    if current_player.id != ctx.authur.id:
        raise IncorrectUser("- Сейчас не Ваша очередь ходить!")


@client.command()
@commands.has_role("Игрок")
async def reraise(ctx):
    current_player = await get_current_player(ctx)
    if current_player.id != ctx.authur.id:
        raise IncorrectUser("- Сейчас не Ваша очередь ходить!")


@client.command()
@commands.has_role("Игрок")
async def check(ctx):
    current_player = await get_current_player(ctx)
    if current_player.id != ctx.authur.id:
        raise IncorrectUser("- Сейчас не Ваша очередь ходить!")


@client.command(name="raise")
@commands.has_role("Игрок")
async def _raise(ctx):
    current_player = await get_current_player(ctx)
    if current_player.id != ctx.authur.id:
        raise IncorrectUser("- Сейчас не Ваша очередь ходить!")


@client.command()
async def leave(ctx):
    await ctx.channel.set_permissions(ctx.author, send_messages=False, read_messages=False)


async def get_current_game_info(ctx):
    pin = await ctx.channel.pins()[0]
    embed = pin.embeds[0]
    raw_data = embed.fields[5].value.split("\n")

    return raw_data[1].split()[0], raw_data[4].split()[0]


async def get_current_player(ctx):
    pin = await ctx.channel.pins()[0]
    embed = pin.embeds[0]
    current_player_line = embed.fields[3].value.split("\n")[4]
    current_player_name, current_player_desc = " ".join(current_player_line.split()[1:]).split("#")

    return get(ctx.guild.members, name=current_player_name, discriminator=current_player_desc)


"""
====================================================================================================================
===================================== РАЗДЕЛ С ПРОЧИМИ КОМАНДАМИ ДЛЯ ИГРОКОВ =======================================
====================================================================================================================
"""


# ФУНКЦИЯ, добавляющая xp, lvl
async def add_level(guild, member_id, xp):
    user = db_sess.query(User).filter(User.id == f"{member_id}-{guild.id}").first()
    user.xp += xp
    need_xp = 50 * (user.level ^ 2) - (50 * user.level)
    if user.xp <= need_xp:
        user.xp = user.xp % need_xp
        user.level += 1
        user.skill_points += 1
    db_sess.commit()


# ФУНКЦИЯ, делающая чистый id пользователя
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

    _name = ' '.join(map(lambda x: x.capitalize(), args))
    user = db_sess.query(User).filter(User.id == f"{member.id}-{guild.id}").first()

    for role in member.roles:
        if role.name == 'Игрок':
            await member.send(':x: **Вы не можете поменять своё имя!** *Для этого обратитесь к администрации.*')
            return
    if user.nation == '-1' or user.origin == '-1':
        await member.send(':x: **Вы не можете создать профиль не выбрав расу и происхождение!**')
        return
    await member.send(':white_check_mark: **Вы успешно создали своего персонажа, удачной игры!**')

    # Устанавливаем имя
    user.name = _name
    # Добавляется роль @Игрок
    role = get(guild.roles, name="Игрок")
    await member.add_roles(role)
    # Изменяем характеристики в зависимости от расы и роль в зависимости от города
    if user.nation == 'Северяне':
        # характеристики
        user.health += 2
        user.strength += 2
        user.intelligence -= 2
        user.dexterity -= 2
        # роль
        role = get(guild.roles, name="Тополис")
    elif user.nation == 'Техно-гики':
        # характеристики
        user.intelligence += 3
        user.dexterity += 1
        user.health -= 1
        user.strength -= 3
        # роль
        role = get(guild.roles, name="Браифаст")
    elif user.nation == 'Южане':
        # характеристики
        user.health += 1
        user.speed += 3
        user.intelligence -= 4
        # роль
        role = get(guild.roles, name="Джадифф")
    await member.add_roles(role)
    # Изменяем характеристики в зависимости от происхождения
    if user.origin == 'Богатая семья':
        # деньги
        user.balance = 14000
        # характеристики
        user.strength -= 2
        user.dexterity -= 2
    elif user.origin == 'Обычная семья':
        # деньги
        user.balance = 4500
        # характеристики
    elif user.origin == 'Бедность':
        # деньги
        user.balance = 500
        # характеристики
        user.strength += 2
        user.dexterity += 2
        user.speed += 2
    # Комит
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
    if city.name not in ["Тополис", "Браифаст", "Джадифф"]:
        raise IncorrectCityName(f"- {city.name} - не является названием существующего города!")

    guild = ctx.guild
    author = ctx.author
    user = db_sess.query(User).filter(User.id == f"{author.id}-{guild.id}").first()

    if city in author.roles:
        raise IncorrectCityName(f"- Вы и так находитесь в {city.name}!")

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


# КОМАНДА, для вливания скилл поинтов в характеристики
@slash.slash(
    name="profile",
    description="Показывает ваши характеристики, сколько у вас свободных очков навыка и прочую информацию.",
    guild_ids=test_servers_id
)
@commands.has_role("Игрок")
async def profile(ctx):
    guild = ctx.guild
    author = ctx.author
    user = db_sess.query(User).filter(User.id == f"{author.id}-{guild.id}").first()
    # ======= ПРОФИЛЬ
    emb = discord.Embed(title=f"⮮ __**{user.name}:**__", color=44444)

    emb.add_field(name='**Баланс:**', value=f"*```yaml\n{user.balance} Gaudium```*", inline=False)
    text1 = f"*```yaml\n" \
            f"Раса ➢ {user.nation}\n" \
            f"Происхождение ➢ {user.origin}```*"
    emb.add_field(name='**Сведения:**', value=text1, inline=False)
    text2 = f"*```yaml\n" \
            f"Здоровье ➢ {user.health}\n" \
            f"Сила ➢ {user.strength}\n"\
            f"Интелект ➢ {user.intelligence}\n" \
            f"Маторика ➢ {user.dexterity}\n" \
            f"Скорость ➢ {user.speed}```*"
    emb.add_field(name='**Характеристики:**', value=text2, inline=False)
    emb.add_field(name='**Свободных очков навыка:**', value=f"*```yaml\n{user.skill_points}```*", inline=False)

    emb.set_thumbnail(url=author.avatar_url)
    emb.set_footer(text=f"Никнейм Discord: {author.name}")

    await ctx.send(embed=emb)


"""
====================================================================================================================
========================================== РАЗДЕЛ С ОБРАБОТЧИКАМИ ОШИБОК ===========================================
====================================================================================================================
"""


@all_in.error
async def all_in_error(ctx, error):
    await throw_error(ctx, error)


@_bet.error
async def bet_error(ctx, error):
    await throw_error(ctx, error)


@call.error
async def call_error(ctx, error):
    await throw_error(ctx, error)


@fold.error
async def fold_error(ctx, error):
    await throw_error(ctx, error)


@reraise.error
async def reraise_error(ctx, error):
    await throw_error(ctx, error)


@_raise.error
async def _raise_error(ctx, error):
    await throw_error(ctx, error)


@check.error
async def check_error(ctx, error):
    await throw_error(ctx, error)


@send_invite_tic_tac_toe.error
async def send_invite_tic_tac_toe_error(ctx, error):
    await throw_error(ctx, error)


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


# Обработчик ошибок функции money_transfer
@money_transfer.error
async def money_transfer_error(ctx, error):
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

    if isinstance(error, MissingRole):
        text = f"- У вас нет роли \"Игрок\" для использования этой команды."
    if isinstance(error, MissingPermissions):
        text = "- У вас недостаточно прав для использования этой команды. (Как иронично)"
    if isinstance(error, CommandNotFound):
        text = "- Неверная команда! Для получения списка команд достаточно нажать \"/\""

    emb = discord.Embed(title="⮮ __**БОТ СТОЛКНУЛСЯ С ОШИБКОЙ:**__", color=0xed4337)
    emb.add_field(name="**Причина:**",
                  value=f"```diff\n{text}\n```",
                  inline=False)
    await ctx.send(embed=emb)


"""
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- ЗАПУСК БОТА -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
"""

DiscordComponents(client)
client.run(TOKEN)
