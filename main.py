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
    print(decision_type)
    if "Взять контракт" in decision_type:
        difficulty = int(embed.fields[3].value.split('**')[1])
        print(difficulty)
        fight = CreateBattle(difficulty)
        await fight.start_battle(guild, member)

    if "Атаковать" in decision_type:
        action = 1

    if "Укрыться" in decision_type:
        action = 2

    if "Лечиться" in decision_type:
        action = 3

    if "Сменить режим стрельбы" in decision_type:
        action = 4

    if "Атаковать" in decision_type:
        action = 5


    if "Начать раздачу" in decision_type:
        dealer_line = embed.fields[3].value.split("\n")[1]
        dealer_name, dealer_desc = " ".join(dealer_line.split()[1:]).split("#")
        dealer = get(guild.members, name=dealer_name, discriminator=dealer_desc)

        if member.id != dealer.id:
            return

        active_card_decks = json.load(open("game_data/active_card_decks.json", encoding="utf8"))
        active_players = json.load(open("game_data/active_players.json", encoding="utf8"))

        deck = DeckOfCards()
        await deck.shuffle()
        active_card_decks[str(message.id)] = deck.cards

        active_players_ids = list(active_players[str(message.id)].keys())

        for player in active_players_ids:
            active_players[str(message.id)][str(player)]["deck"] = await deck.take(2)

        player_id = 4 if 3 < len(active_players_ids) else 4 % len(active_players_ids)
        old_field_value = "\n".join(embed.fields[3].value.split("\n")[:4])

        embed.set_field_at(3, name="\u200b",
                           value=f"{old_field_value}\n"
                                 f"{player_id + 1}.\t{guild.get_member(int(active_players_ids[player_id]))}\n"
                                 f"Ход раунда: 1 из {len(active_players_ids)}",
                           inline=True)

        await interaction.send("Раздача завершена!")
        await message.edit(embed=embed,
                           components=[Button(style=ButtonStyle.gray, label="Посмотреть свои карты")])

        await commit_changes(active_card_decks, "game_data/active_card_decks.json")
        await commit_changes(active_players, "game_data/active_players.json")

        return

    if "Посмотреть свои карты" in decision_type:
        active_players = json.load(open("game_data/active_players.json", encoding="utf8"))
        if str(member.id) not in list(active_players[str(message.id)].keys()):
            await interaction.send(":x: Вы не участвуйте в этой игре!")
            return

        player_cards = active_players[str(message.id)][str(member.id)]["deck"]
        text_cards = []
        for card_info in player_cards:
            value, suit = card_info.split(" - ")
            text_cards.append(f"{value} {client.get_emoji(playing_cards_emoji[suit])}")
        text_cards = "\t\t".join(text_cards)

        await interaction.send(f"Ваши карты:\n\t{text_cards}")
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

            user_balance = db_sess.query(User).filter(User.id == f"{user.id}-{_message.guild.id}").first().balance
            bet = int(text.split("\n")[2].split()[6])
            if user_balance < bet:
                await _message.channel.send(":x: У вас недостаточно средств для начала игры!")
                await reaction.remove(user)
                return
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
        embed = _message.embeds[0]
        if embed.fields[0].value.split()[1][:-1] == user.name:
            # num = 0
            # for i in range(1, 10):
            #     if numbers_emoji[i] == _emoji:
            #         num = i
            #         break
            #
            # p1 = embed.fields[0].value.split()[1][:-1]
            # p2, p3 = embed.footer.text.split()[1][:-1], embed.footer.text.split()[3]
            # player = p2 if p1 == p2 else p3
            #
            # cross_and_zero = []
            # count = 1
            # for elem in embed.fields[1].value:
            #     if elem in ['❌', '⭕']:
            #         if count == num:
            #             if player == p2:
            #                 elem = '❌'
            #         cross_and_zero.append(elem)
            #         count += 1
            # print(cross_and_zero)
            #
            # embed.fields[0].value = f"*Ходит: {p2 if player != p2 else p3}*"
            #
            # await msg.edit(embed=embed)

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
    embed = discord.Embed(title='⮮ __**Выбор расы:**__', color=44444)
    embed.add_field(name='**Важно:**', value=text, inline=False)

    await channel.send(
        embed=embed,
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
    embed = discord.Embed(title='⮮ __**Выбор происхождения:**__', color=44444)
    embed.add_field(name='**Важно:**', value=text, inline=False)

    await channel.send(
        embed=embed,
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
    embed = discord.Embed(title='⮮ __**Ваше имя:**__', color=44444)
    embed.add_field(name='**Важно:**', value=text, inline=False)

    await channel.send(embed=embed)


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
    embed = discord.Embed(title='⮮ __**История:**__', color=44444)
    embed.add_field(name='**――**', value=text, inline=False)

    await channel.send(embed=embed)

    # ======= Инфо
    text = '*```yaml\n' \
           '➢ Для того что бы узнать команды, напишите в чате "/", вам предоставится список команд с их описаниями.' \
           '➢ Основная валюта игры - Gaudium.' \
           '➢ Если у вас возникла ошибка обращайтесь к администрации.```*'
    embed = discord.Embed(title='⮮ __**Правила:**__', color=44444)
    embed.add_field(name='**――**', value=text, inline=False)

    await channel.send(embed=embed)


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
            embed = discord.Embed(title=f"⮮ __**{_type['NAME']}:**__", color=0xf1c40f)
            for item in items:
                embed.add_field(
                    name=f"**{item.name}:**",
                    value=f"➢ **Цена:** {item.price} {client.get_emoji(emoji['money'])}"
                          f"```fix\nОписание: {item.description} Тип: {_type[item.type]}```", inline=False
                )
            # Кнопки для покупки
            buttons = [Button(style=ButtonStyle.gray, label=f"Купить {item.name}") for item in items]
            # Отправка сообщения
            await store_channel.send(
                embed=embed,
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
    player_db = db_sess.query(User).filter(User.id == f"{player.id}-{guild.id}").first()
    embed = discord.Embed(title=f"**˹ Инвентарь __{player_db.name.upper()}__˼**",
                          description=f"Баланс: {player_db.balance} Gaudium", color=0xFFFFF0)

    if len(player_inventory.keys()) != 0:
        item_id = 1
        for item, amount in player_inventory.items():
            item_obj = db_sess.query(Items).filter(Items.name == item).first()
            text = f"**Порядковый ID:** *{item_id}*\n" \
                   f"**Количество:** *{amount}*\n" \
                   f"**Цена:** *{item_obj.price} {value_emoji}*\n" \
                   f"**Описание:** *{item_obj.description}*"

            embed.add_field(name=f"**{item.upper()}:**",
                            value=text,
                            inline=True)
            item_id += 1
    else:
        embed.add_field(name="Полностью пуст", value="\u200b")

    embed.set_thumbnail(url=player.avatar_url)
    embed.set_footer(text=f"Никнейм Discord: {player.name}")

    await ctx.send(embed=embed)
"""
====================================================================================================================
============================================= РАЗДЕЛ С СОЗДАНИЕМ МИССИЙ ============================================
====================================================================================================================
"""


@slash.slash(name="mission_run",
             description="Генерирует миссии на досках объявлений.",
             options=[{"name": "amount", "description": "количество контрактов в городах",
                       "type": 3, "required": False}],
             guild_ids=test_servers_id)
async def mission_run(ctx, amount=5):
    a = TownMissions(int(amount))
    await a.add_missions()


class TownMissions:
    def __init__(self, amount):
        self.missions = []
        self.town_letters = ['т', 'б', 'д']
        self.amount = amount
        self.aim = {'find_him': 'Найти и уничожить', 'stolen_item': 'Вернуть украденную вешь владельцу',
                    'foreign territory': 'Уничтожить отряд противника',
                    'old_tech': 'Разведать обозначенную учёными местность'}
        self.scenario_to_dif = {'find_him': False, 'stolen_item': False, 'foreign territory': True, 'caravan': False,
                                'old_tech': True}

    async def add_missions(self):
        with open('scenarios.json', encoding="utf8") as scenarios:
            req = json.load(scenarios)
            scenario = req['missions']
            items = req['items']
        for elem in self.town_letters:
            for i in range(self.amount):
                scen = random.choice(list(scenario.keys()))
                diff = random.randint(1, 2)
                if scen != 'stolen_item':
                    if self.scenario_to_dif[scen]:
                        diff = 3
                    self.missions.append(
                        {'time': random.randint(1, 60), 'difficulty': diff, 'descript': random.choice(scenario[scen]),
                         'aim': self.aim[scen]})
                else:
                    line = random.choice(scenario[scen])
                    line = line.replace('item', random.choice(items))
                    self.missions.append(
                        {'time': random.randint(1, 60), 'difficulty': diff, 'descript': line,
                         'aim': self.aim[scen]})
            print(self.missions)
            await self.show_mission(elem)
            self.missions = []

    async def show_mission(self, letter):
        for guild in client.guilds:
            print(guild)
            print(guild.text_channels)
            channel = discord.utils.get(guild.text_channels, name=f"📋доска-объявлений-{letter}")
            if channel is not None:
                for elem in self.missions:
                    embed = discord.Embed(title=f"Доступен контракт", color=discord.Colour.from_rgb(255, 160, 122))
                    embed.add_field(name="\u200b", value=f"```{elem['descript']}```", inline=False)
                    embed.add_field(name="**Цель:**", value=f"**{elem['aim']}**", inline=True)
                    embed.add_field(name="\u200b", value="\u200b", inline=True)
                    embed.add_field(name="**Сложность:**", value=f"**{elem['difficulty']}**", inline=True)
                    await channel.send(embed=embed, components=[Button(style=ButtonStyle.blue, label="Взять контракт")])


class CreateBattle:
    def __init__(self, dif):
        self.difficulty = dif
        self.names = ['Лёха', 'Андрюха', 'Виталя', 'Жека', 'Гена', 'Влад', 'Дима', 'Юра', 'Олег', 'Миша', 'Ден', 'Макс',
                      'Вова', 'Арсюха', 'Марк', 'Тарас', 'Колян', 'Даня', 'Паша', 'Лёня', 'Кирилл', 'Ян', 'Денис']
        self.sir_names = ['Хмырь', 'Бульдозер', 'Шустрый', 'Фольга', 'Вобла', 'Татарин', 'Цыган', 'Колдун', 'Борода',
                          'Фин', 'Шаман', 'Бестолочь', 'Южанин', 'Бочка', 'Сокол', 'Батон', 'Чёрт', 'Чугун', 'Воробей',
                          'Химик', 'Крот', 'Бастард', 'Окурок', 'Ясень', 'Токарь', 'Кувалда', 'Шпала', 'Рябой',
                          'Копатель']

    async def create_buddies(self):
        name = f'{random.choice(self.names)} {random.choice(self.sir_names)}'
        mag_cap = random.choice([5, 15, 30, 60])
        fire_mods = ['semi']
        if mag_cap == 15:
            fire_mods.append('pew - pew')
        if mag_cap >= 30:
            fire_mods.append('auto')
        if self.difficulty == 1:
            return {'fight_stats': {'hp': random.randint(20, 40), 'armor': random.randint(5, 15),
                                    'damage': random.randint(7, 15), 'aim': random.randint(5, 14), 'mag': mag_cap,
                                    'max_mag': mag_cap, 'fire_mods': fire_mods, 'cur_mod': random.choice(fire_mods)},
                    'stats': {'race_bonus': 0, 'streight': random.randint(5, 10), 'intel': random.randint(5, 10),
                              'motor': random.randint(5, 10), 'speed': random.randint(5, 10), 'name': name}}
        elif self.difficulty == 2:
            return {'fight_stats': {'hp': random.randint(30, 60), 'armor': random.randint(10, 35),
                                    'damage': random.randint(14, 30), 'aim': random.randint(10, 18), 'mag': mag_cap,
                                    'max_mag': mag_cap, 'fire_mods': fire_mods, 'cur_mod': random.choice(fire_mods)},
                    'stats': {'race_bonus': 0, 'streight': random.randint(10, 17), 'intel': random.randint(10, 17),
                              'motor': random.randint(10, 17), 'speed': random.randint(10, 17), 'name': name}}
        elif self.difficulty == 3:
            return {'fight_stats': {'hp': random.randint(40, 80), 'armor': random.randint(25, 60),
                                    'damage': random.randint(20, 45), 'aim': random.randint(20, 29), 'mag': mag_cap,
                                    'max_mag': mag_cap, 'fire_mods': fire_mods, 'cur_mod': random.choice(fire_mods)},
                    'stats': {'race_bonus': 0, 'streight': random.randint(20, 30), 'intel': random.randint(20, 34),
                              'motor': random.randint(30, 50), 'speed': random.randint(30, 40), 'name': name}}

    async def start_battle(self, guild, member):
        dil = {'fight_stats': {'hp': 4000, 'armor': 15, 'damage': 7, 'aim': 7, 'mag': 10, 'max_mag': 15,
                               'fire_mods': ['semi', 'pew - pew', 'auto'], 'cur_mod': 'semi'},
               'stats': {'race_bonus': 15, 'streight': 10, 'intel': 9, 'motor': 20, 'speed': 7, 'name': 'tester'}}

        enemy = []
        dif_to_count = {1: (1, 5), 2: (2, 4), 3: (1, 3)}
        diap = dif_to_count[self.difficulty]
        for i in range(random.randint(diap[0], diap[1])):
            enemy.append(Person(self.create_buddies()))
        print(member)
        channel_name = f"комната {''.join(filter(str.isalnum, member.name))}"
        channel = get(guild.channels, name=channel_name)
        if channel:
            await channel.delete()
        channel = await guild.create_text_channel(channel_name, category=guild.categories[2])
        await channel.set_permissions(guild.default_role, send_messages=False, read_messages=False)
        await channel.set_permissions(member, send_messages=True, read_messages=True)
        start = Battle(channel)
        await start.add_persons([[Person(dil)], enemy])


class Battle:
    def __init__(self, channel):
        self.warriors = {'player': [], 'enemy': []}
        self.queue = 'Player'
        self.channel = channel

    async def add_persons(self, persons):
        self.warriors['player'] = persons[0]
        self.warriors['enemy'] = persons[1]
        await self.turn()

    @staticmethod
    async def win_lose(win):
        if win:
            print('УраПобеда')
        else:
            print('____')
            print('Поражение')

    async def turn(self):
        od = 5
        more = True
        player = self.warriors['player'][0]
        await self.channel.send('**___Ваш ход___**')
        while od != 0:
            fight_stats = await player.get_fight_stats()
            embed = discord.Embed(title=f"Ваши Показатели", color=discord.Colour.from_rgb(0, 255, 0))
            embed.add_field(name="**Ваше ОЗ**", value=fight_stats['hp'], inline=True)
            embed.add_field(name="**Ваша Защита**", value=fight_stats['armor'], inline=True)
            await self.channel.send(embed=embed, components=[[Button(style=ButtonStyle.red, label="Атаковать"),
                Button(style=ButtonStyle.blue, label="Укрыться"),
                Button(style=ButtonStyle.green, label="Лечиться"),
                Button(style=ButtonStyle.gray, label="Сменить режим стрельбы")]])
            a = a
            if action == 1:
                for elem in self.warriors['enemy']:
                    print(f'{self.warriors["enemy"].index(elem) + 1}) {elem.get_info()}')
                action = int(input())
                a = await self.attack(self.warriors['enemy'][action - 1], player)
                if a > 0:
                    print(f'Вы нанесли урон в размере {a} hp')
                    if self.warriors['enemy'][action - 1].get_fight_stats()['hp'] <= 0:
                        self.warriors['enemy'].remove(self.warriors['enemy'][action - 1])
                        if len(self.warriors['enemy']) == 0:
                            await self.win_lose(True)
                            more = False
                            break
                else:
                    print('Вы не смогли нанести противнику урон')
                od -= 1
            elif action == 2:
                action = 1
                while action != 2 and od != 0:
                    a = await self.hide(player)
                    if a >= 0:
                        print(f'Вы спрятались, ваша защита стала {a} единиц')
                    else:
                        print('Вы не смогли спрятаться')
                    print('1) Сменить позицию')
                    print('2) Остаться')
                    od -= 1
                    action = input()
            elif action == 3:
                if self.warriors['player'][0].get_fight_stats()['mag'] == \
                        self.warriors['player'][0].get_fight_stats()['max_mag']:
                    print('Перезарядка не требуется')
                else:
                    base_motor = 15 + player.get_stats()['motor']
                    action = 1
                    while action != 2 and od != 0:
                        a = random.randint(1, 100)
                        if a <= base_motor:
                            action = 2
                            player.reload()
                            print(player.get_fight_stats()['mag'])
                            print('Вы успешно перезарядили оружие')
                        else:
                            print('Вы не смогли перезарядить оружие')
                            print('1) Повторить попытку')
                            print('2) Оставить')
                            action = input()
                        od -= 1

            elif action == '4':
                heal = 15 + random.randint(1, player.get_stats()['intel'] // 2)
                print(f'Вы восполнили своё здоровье на {heal} hp')
                player.heal(heal)
                od -= 1
            elif action == '5':
                print(player.change_mode())
        if more:
            print('___ход противника___')
        for elem in self.warriors['enemy']:
            print(f'__ {elem.get_stats()["name"]} __')
            od = 5
            warrior = elem
            heal_point, hide_point, armor_point, min_mag = warrior.get_static_fight_stats()
            while od >= 1:
                warrior_stats = warrior.get_fight_stats()
                if (warrior_stats['hp'] < hide_point and warrior_stats['armor'] >= armor_point) or \
                        warrior_stats['hp'] < heal_point:
                    heal = 4 + random.randint(1, warrior.get_stats()['intel'] // 2)
                    print(f'Противник восполнил своё здоровье на {heal} hp')
                    warrior.heal(heal)
                    od -= 1
                elif warrior_stats['hp'] < hide_point and warrior_stats['armor'] <= armor_point:
                    print('ща как сныкаюсь')
                    a = await self.hide(warrior)
                    if a >= 0:
                        print(f'Противник спрятался, его защита возросла на {a} единиц')
                    else:
                        print('Противник не смог спрятаться')
                    od -= 1
                elif warrior_stats['mag'] <= min_mag:
                    print('ПЕРЕЗАРЯЖАЮСЬ')
                    if warrior_stats['mag'] != warrior_stats['max_mag']:
                        base_motor = 15 + warrior.get_stats()['motor']
                        a = random.randint(1, 100)
                        if a <= base_motor:
                            warrior.reload()
                            print('Противник успешно перезарядил оружие')
                        else:
                            print('Противник не смог перезарядить оружие')
                        od -= 1
                else:
                    print('Пизда тебе капчёный')
                    dealed_damage = await self.attack(self.warriors['player'][0], warrior)
                    if dealed_damage > 0:
                        print(f'Вам нанесли урон в размере {dealed_damage} hp')
                        if player.get_fight_stats()['hp'] <= 0:
                            await self.win_lose(False)
                            more = False
                            break
                    od -= 1

            if not more:
                break
            print('____')
        if more:
            await self.turn()

    @staticmethod
    async def hide(warrior):
        base_speed = 15 + warrior.get_stats()['speed']
        arm_bonus = {'field': 0, 'tree': 15, 'rock': 20, 'baricade': 30}
        a = random.randint(1, 100)
        if a <= base_speed:
            hide = random.choice(('field', 'tree', 'rock', 'baricade'))
            warrior.add_get_clear_bonus('add', 'armor+', arm_bonus[hide])
            return arm_bonus[hide] + warrior.get_fight_stats()['armor']
        else:
            return 0

    @staticmethod
    async def attack(target, warrior):
        base_aim = 30
        fire_mode = warrior.get_fight_stats()['cur_mod']
        mag = warrior.get_fight_stats()['mag']
        play_damage = warrior.get_fight_stats()['damage']
        play_aim = warrior.get_fight_stats()['aim']
        en_armor = target.get_fight_stats()['armor']
        total_damage = 0
        if 'aim+' in warrior.add_get_clear_bonus('get'):
            base_aim += warrior.add_get_clear_bonus('get')['aim+']
        if fire_mode == 'semi' and mag >= 1:
            shoots = 1
            warrior.shoot(1)
        elif fire_mode == 'pew - pew' and mag >= 3:
            warrior.shoot(3)
            shoots = 3
            base_aim -= 20
        elif fire_mode == 'auto' and mag >= 10:
            warrior.shoot(10)
            shoots = 10
            base_aim -= 25
        else:
            print('Недостаточно патронов')
            shoots = 0
        for i in range(shoots):
            if random.randint(1, 100) <= base_aim + play_aim and play_damage > en_armor * 0.01:
                target.get_hurt(play_damage - en_armor * 0.01)
                warrior.add_get_clear_bonus('clear', 'aim+')
                total_damage += play_damage - en_armor * 0.01
            else:
                warrior.add_get_clear_bonus('add', 'aim+', 10)

        return total_damage


class Person:
    def __init__(self, stats={}):
        if stats == {}:
            self.stats = {'fight_stats': {'hp': 0, 'armor': 0, 'damage': 0, 'aim': 0, 'mag': 0, 'max_mag': 0,
                                          'fire_mods': [], 'cur_mod': ''},
                          'stats': {'race_bonus': 0, 'streight': 0, 'intel': 0, 'motor': 0, 'speed': 0, 'name': ''}}
        else:
            self.stats = stats
        self.static_stats = stats
        self.bonuses = {}

    async def load_person(self, stats):
        self.stats = stats

    async def get_hurt(self, damage):
        self.stats['fight_stats']['hp'] = round((self.stats['fight_stats']['hp'] - damage), 2)

    async def get_info(self):
        info = str(self.stats["fight_stats"]["hp"]), str(self.stats["fight_stats"]["armor"]), \
               str(self.stats["fight_stats"]["damage"])
        return f'{self.stats["stats"]["name"]} [{" ".join(info)}]'

    async def get_fight_stats(self):
        return self.stats['fight_stats']

    async def get_static_fight_stats(self):
        mode_to_minimum = {'auto': 10, 'pew - pew': 3, 'semi': 1}
        hide_hp = self.static_stats['fight_stats']['hp'] - self.static_stats['fight_stats']['hp'] / 3
        heal_hp = self.static_stats['fight_stats']['hp'] - self.static_stats['fight_stats']['hp'] / 4
        mininmum_ammo_amount = mode_to_minimum[self.static_stats['fight_stats']['cur_mod']]
        armor = self.static_stats['fight_stats']['armor'] + self.static_stats['fight_stats']['armor'] * 0.03
        return hide_hp, heal_hp, armor, mininmum_ammo_amount

    async def get_stats(self):
        return self.stats['stats']

    async def reload(self):
        self.stats['fight_stats']['mag'] = self.stats['fight_stats']['max_mag']

    async def heal(self, heal):
        self.stats['fight_stats']['hp'] = round((self.stats['fight_stats']['hp'] + heal), 2)

    async def shoot(self, amount):
        self.stats['fight_stats']['mag'] -= amount

    async def change_mode(self):
        avalible_mods = self.stats['fight_stats']['fire_mods']
        cur_mod = self.stats['fight_stats']['cur_mod']
        if avalible_mods.index(cur_mod) + 1 >= len(avalible_mods):
            cur_mod = avalible_mods[0]
        else:
            cur_mod = avalible_mods[avalible_mods.index(cur_mod) + 1]
        self.stats['fight_stats']['cur_mod'] = cur_mod
        return cur_mod

    async def add_get_clear_bonus(self, *args):
        to_do = args[0]
        if len(args) > 1:
            name = args[1]
            if to_do == 'add':
                num = args[2]
                if name in self.bonuses:
                    self.bonuses[name] += num
                else:
                    self.bonuses[name] = num
            if to_do == 'clear':
                if name in self.bonuses:
                    self.bonuses[name] = 0
        elif to_do == 'get':
            return self.bonuses

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
    # Сообщение-поле игры   |   (❌ or ⭕ | embed.set_footer(text=f""))
    embed = discord.Embed(title=f"**<<= КРЕСТИКИ-НОЛИКИ =>>**", color=44444)
    embed.add_field(name="**. ━━━━━━━━━━━━━━ .**", value=f"*Ходит: {cross_and_zero[0]}*", inline=False)
    text = f"**▫〰{'🔲'}〰 | 〰{'🔲'}〰 | 〰{'🔲'}〰▫**\n" \
           f"**. ━━━━━━━━━━━━━━ .**\n" \
           f"**▫〰{'🔲'}〰 | 〰{'🔲'}〰 | 〰{'🔲'}〰▫**\n" \
           f"**. ━━━━━━━━━━━━━━ .**\n" \
           f"**▫〰{'🔲'}〰 | 〰{'🔲'}〰 | 〰{'🔲'}〰▫**\n" \
           f"**. ━━━━━━━━━━━━━━ .**"
    embed.add_field(name="**. ━━━━━━━━━━━━━━ .**", value=text, inline=False)
    embed.set_footer(text=f"Крестики: {cross_and_zero[0]}; Нолики: {cross_and_zero[1]}")

    msg = await channel.send(embed=embed)

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
    raw_member_data = members.split("><")
    members = [guild.get_member(await clean_member_id(member_id)) for member_id in raw_member_data]

    if ctx.author not in members:
        members.append(ctx.author)

    if "таверна" not in ctx.channel.name:
        raise ChannelNameError(f"- Эта команда работает только в тавернах разных городов.\n"
                               f"В канале {ctx.channel} эту команду использовать нельзя!")
    if not 2 <= len(members) <= 5:
        raise IncorrectMemberAmount(f"- Неверное количество игроков!\n"
                                    f"Для игры в покер нужно от 2 до 5 человек. У вас - {len(members)}.")

    for member in members:
        if member.bot:
            raise IncorrectUser(f"- Выбран неверный пользователь.\n{member.name} - бот!")
        if get(guild.roles, name="Игрок") not in member.roles:
            raise IncorrectUser(f"- Выбран неверный пользователь.\nУ {member.name} нет роли \"Игрок\"!")

    user_balance = db_sess.query(User).filter(User.id == f"{ctx.author.id}-{guild.id}").first().balance
    if bet < 10:
        raise IncorrectBetAmount(f"- Нельзя ставить ставку, которая меньше минимальной (10 Gaudium)")
    if bet > user_balance:
        raise IncorrectBetAmount(f"- Ставка {bet} Gaudium не может быть применена, "
                                 f"так как у Вас нет достаточной суммы.\n"
                                 f"Ваш баланс: {user_balance} Gaudium")

    channel_name = f"poker-lobby-{''.join(filter(str.isalnum, ctx.author.name))}".lower()
    channel = get(guild.channels, name=channel_name)
    if channel:
        await channel.delete()

    channel = await guild.create_text_channel(channel_name, category=ctx.channel.category)

    await channel.set_permissions(guild.default_role, send_messages=False, read_messages=False)
    for member in members:
        await channel.set_permissions(member, send_messages=True, read_messages=True)

    games_history = json.load(open("game_data/games_history.json"))
    games_history[str(channel.id)] = 0

    members_list = "\n".join([member.mention for member in members])
    value_emoji = client.get_emoji(emoji["money"])
    await ctx.send(f"Лобби {channel.mention} создано.\n"
                   f"{members_list}")
    message = await channel.send(f"**ЖДЁМ НАЧАЛА ИГРЫ!**\n"
                                 f"Чтобы принять участие в партии покера, нажмите кнопку ✅\n"
                                 f"*NB! Для игры, нужно иметь, минимум {bet} {value_emoji}*\n"
                                 f"**__Текущие участники:__**\n"
                                 f"᲼᲼᲼Отсутствуют :(")
    await message.add_reaction("✅")
    await message.pin()

    await commit_changes(games_history, "game_data/games_history.json")


@client.command()
@commands.has_role("Игрок")
async def play(ctx):
    guild = ctx.guild
    channel = ctx.channel
    pins = await channel.pins()
    message_text = pins[-1].content

    games_history = json.load(open("game_data/games_history.json"))

    bet = int(message_text.split("\n")[2].split()[6])
    members_ids = [await clean_member_id(member.split("  ")[-1]) for member in message_text.split("\n")[4:]]
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

    members_text = await get_formatted_players(members, guild.id, value_emoji)

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
    embed.add_field(name="\u200b", value=f"**Последнее действие:**\n"
                                         f"Собраны блайнды с игроков:\n"
                                         f"  {members[small_blind_id]}\n"
                                         f"  {members[blind_id]}", inline=True)

    # await pins[0].unpin()
    message = await ctx.send(embed=embed,
                             components=[Button(style=ButtonStyle.green, label="Начать раздачу")])
    await message.pin()

    active_players = json.load(open("game_data/active_players.json", encoding="utf8"))

    games_history[str(channel.id)] += 1
    active_players[str(message.id)] = {}
    for member_id in members_ids:
        active_players[str(message.id)][member_id] = {"deck": [], "bet": 0, "action": ""}

    await commit_changes(games_history, "game_data/games_history.json")
    await commit_changes(active_players, "game_data/active_players.json")
    db_sess.commit()


@client.command(name="bet")
@commands.has_role("Игрок")
async def _bet(ctx, bet_amount):
    current_game_data = await get_current_game_data(ctx)

    if current_game_data["current_player"].id != ctx.author.id:
        raise IncorrectUser("- Сейчас не Ваша очередь ходить!")
    if current_game_data["current_player_id"] != 1:
        raise IncorrectGameAction("- Команду /bet можно использовать только в первый ход раунда!")

    all_active_players = json.load(open("game_data/active_players.json", encoding="utf8"))
    active_players = all_active_players[str(current_game_data["message"].id)]

    guild = ctx.guild

    new_min_bet = current_game_data["min_bet"]
    player_bet = int(bet_amount) if int(bet_amount) >= new_min_bet else new_min_bet
    new_min_bet = player_bet

    user = db_sess.query(User).filter(User.id == f"{ctx.author.id}-{guild.id}").first()
    action = f"{ctx.author} сделал bet на {player_bet} {client.get_emoji(emoji['money'])}"

    all_active_players[str(current_game_data["message"].id)][str(ctx.author.id)]["bet"] = player_bet
    all_active_players[str(current_game_data["message"].id)][str(ctx.author.id)]["action"] = "bet"

    if player_bet >= user.balance:
        action = f"{ctx.author} пошёл в all-in!"
        player_bet = user.balance
        all_active_players[str(current_game_data["message"].id)][str(ctx.author.id)]["action"] = "all-in"

    user.balance -= player_bet

    next_player_id, next_player = await get_next_player(current_game_data["min_bet"], active_players, guild)
    new_game_data = {
        "next_player": next_player,
        "next_player_id": next_player_id,
        "max_player_id": current_game_data["max_player_id"],
        "new_pot": current_game_data["pot"] + player_bet,
        "new_min_bet": new_min_bet,
        "last_action": action
    }

    db_sess.commit()
    await commit_changes(all_active_players, "game_data/active_players.json")
    await commit_game_changes(current_game_data["message"], new_game_data, guild)


@client.command()
@commands.has_role("Игрок")
async def call(ctx):
    current_game_data = await get_current_game_data(ctx)

    if current_game_data["current_player"].id != ctx.author.id:
        raise IncorrectUser("- Сейчас не Ваша очередь ходить!")

    all_active_players = json.load(open("game_data/active_players.json", encoding="utf8"))
    active_players = all_active_players[str(current_game_data["message"].id)]

    guild = ctx.guild
    player_bet = current_game_data["min_bet"]
    new_min_bet = player_bet

    user = db_sess.query(User).filter(User.id == f"{ctx.author.id}-{guild.id}").first()
    action = f"{ctx.author} поддержал ставку {player_bet} {client.get_emoji(emoji['money'])}"

    all_active_players[str(current_game_data["message"].id)][str(ctx.author.id)]["bet"] = player_bet
    all_active_players[str(current_game_data["message"].id)][str(ctx.author.id)]["action"] = "bet"

    if player_bet >= user.balance:
        action = f"{ctx.author} пошёл в all-in!"
        player_bet = user.balance
        all_active_players[str(current_game_data["message"].id)][str(ctx.author.id)]["action"] = "all-in"

    user.balance -= player_bet

    next_player_id, next_player = await get_next_player(current_game_data["min_bet"], active_players, guild)
    new_game_data = {
        "next_player": next_player,
        "next_player_id": next_player_id,
        "max_player_id": current_game_data["max_player_id"],
        "new_pot": current_game_data["pot"] + player_bet,
        "new_min_bet": new_min_bet,
        "last_action": action
    }

    db_sess.commit()
    await commit_game_changes(current_game_data["message"], new_game_data, guild)


@client.command()
@commands.has_role("Игрок")
async def fold(ctx):
    current_game_data = await get_current_game_data(ctx)

    if current_game_data["current_player"].id != ctx.author.id:
        raise IncorrectUser("- Сейчас не Ваша очередь ходить!")

    guild = ctx.guild
    action = f"{ctx.author} вышел из игры"

    all_active_players = json.load(open("game_data/active_players.json", encoding="utf8"))
    active_players = all_active_players[str(current_game_data["message"].id)]
    active_players_ids = list(all_active_players[str(current_game_data["message"].id)].keys())
    current_player = active_players_ids[current_game_data["current_player_id"] - 1]

    if len(active_players_ids) - 1 == 1:
        await poker_win(ctx)
        return

    next_player_id, next_player = await get_next_player(current_game_data["min_bet"], active_players, guild)
    new_game_data = {
        "next_player": next_player,
        "next_player_id": next_player_id,
        "max_player_id": current_game_data["max_player_id"] - 1,
        "new_pot": current_game_data["pot"],
        "new_min_bet": current_game_data["min_bet"],
        "last_action": action
    }

    del all_active_players[str(current_game_data["message"].id)][current_player]

    db_sess.commit()
    await commit_changes(all_active_players, "game_data/active_players.json")
    await commit_game_changes(current_game_data["message"], new_game_data, guild)


@client.command()
@commands.has_role("Игрок")
async def all_in(ctx):
    current_game_data = await get_current_game_data(ctx)

    if current_game_data["current_player"].id != ctx.author.id:
        raise IncorrectUser("- Сейчас не Ваша очередь ходить!")

    all_active_players = json.load(open("game_data/active_players.json", encoding="utf8"))
    active_players = all_active_players[str(current_game_data["message"].id)]

    guild = ctx.guild
    user = db_sess.query(User).filter(User.id == f"{ctx.author.id}-{guild.id}").first()
    player_bet = user.balance

    action = f"{ctx.author} пошёл в all-in!"
    user.balance = 0

    all_active_players[str(current_game_data["message"].id)][str(ctx.author.id)]["bet"] = player_bet
    all_active_players[str(current_game_data["message"].id)][str(ctx.author.id)]["action"] = "all-in"

    next_player_id, next_player = await get_next_player(current_game_data["min_bet"], active_players, guild)
    new_game_data = {
        "next_player": next_player,
        "next_player_id": next_player_id,
        "max_player_id": current_game_data["max_player_id"],
        "new_pot": current_game_data["pot"] + player_bet,
        "new_min_bet": player_bet,
        "last_action": action
    }

    db_sess.commit()
    await commit_changes(all_active_players, "game_data/active_players.json")
    await commit_game_changes(current_game_data["message"], new_game_data, guild)


@client.command()
@commands.has_role("Игрок")
async def check(ctx):
    current_game_data = await get_current_game_data(ctx)

    if current_game_data["current_player"].id != ctx.author.id:
        raise IncorrectUser("- Сейчас не Ваша очередь ходить!")

    all_active_players = json.load(open("game_data/active_players.json", encoding="utf8"))
    active_players = all_active_players[str(current_game_data["message"].id)]

    previous_bet = active_players[str(current_game_data["current_player_id"] - 2)]["bet"]
    players_bet = active_players[str(current_game_data["current_player_id"] - 1)]["bet"]
    if previous_bet != players_bet:
        raise IncorrectGameAction(f"- Команду /check можно использовать, если предыдущая ставка равна Вашей!\n"
                                  f"Ваша ставка - {players_bet} Gaudium для использования "
                                  f"этой команды нужно - {previous_bet} Gaudium")

    guild = ctx.guild

    action = f"{ctx.author} пропустил ход"
    all_active_players[str(current_game_data["message"].id)][str(ctx.author.id)]["action"] = "check"

    next_player_id, next_player = await get_next_player(current_game_data["min_bet"], active_players, guild)
    new_game_data = {
        "next_player": next_player,
        "next_player_id": next_player_id,
        "max_player_id": current_game_data["max_player_id"],
        "new_pot": current_game_data["pot"],
        "new_min_bet": current_game_data["min_bet"],
        "last_action": action
    }

    await commit_changes(all_active_players, "game_data/active_players.json")
    await commit_game_changes(current_game_data["message"], new_game_data, guild)


@client.command(name="raise")
@commands.has_role("Игрок")
async def _raise(ctx, raise_amount):
    current_game_data = await get_current_game_data(ctx)

    if current_game_data["current_player"].id != ctx.author.id:
        raise IncorrectUser("- Сейчас не Ваша очередь ходить!")

    all_active_players = json.load(open("game_data/active_players.json", encoding="utf8"))
    active_players = all_active_players[str(current_game_data["message"].id)]

    guild = ctx.guild

    new_min_bet = current_game_data["min_bet"]
    player_raise = int(raise_amount) if int(raise_amount) >= new_min_bet * 2 else new_min_bet * 2
    new_min_bet = player_raise

    user = db_sess.query(User).filter(User.id == f"{ctx.author.id}-{guild.id}").first()
    action = f"{ctx.author} повысил ставку на {player_raise} {client.get_emoji(emoji['money'])}"

    all_active_players[str(current_game_data["message"].id)][str(ctx.author.id)]["bet"] = player_raise
    all_active_players[str(current_game_data["message"].id)][str(ctx.author.id)]["action"] = "raise"

    if player_raise >= user.balance:
        action = f"{ctx.author} пошёл в all-in!"
        player_raise = user.balance
        all_active_players[str(current_game_data["message"].id)][str(ctx.author.id)]["action"] = "all-in"

    user.balance -= player_raise

    changed_players_amount = await get_all_next_players(new_min_bet, active_players)
    next_player_id, next_player = await get_next_player(new_min_bet, active_players, guild)
    new_game_data = {
        "next_player": next_player,
        "next_player_id": next_player_id,
        "max_player_id": current_game_data["max_player_id"] + changed_players_amount,
        "new_pot": current_game_data["pot"] + player_raise,
        "new_min_bet": new_min_bet,
        "last_action": action
    }

    db_sess.commit()
    await commit_changes(all_active_players, "game_data/active_players.json")
    await commit_game_changes(current_game_data["message"], new_game_data, guild)


@client.command()
@commands.has_role("Игрок")
async def reraise(ctx, raise_amount):
    current_game_data = await get_current_game_data(ctx)

    if current_game_data["current_player"].id != ctx.author.id:
        raise IncorrectUser("- Сейчас не Ваша очередь ходить!")

    all_active_players = json.load(open("game_data/active_players.json", encoding="utf8"))
    active_players = all_active_players[str(current_game_data["message"].id)]

    if active_players[str(current_game_data["current_player_id"] - 2)]["action"] != "raise":
        raise IncorrectGameAction("- Команду /reraise можно использовать только после /raise")

    guild = ctx.guild

    new_min_bet = current_game_data["min_bet"]
    player_raise = int(raise_amount) if int(raise_amount) >= new_min_bet * 2 else new_min_bet * 2
    new_min_bet = player_raise

    user = db_sess.query(User).filter(User.id == f"{ctx.author.id}-{guild.id}").first()
    action = f"{ctx.author} повысил ставку на {player_raise} {client.get_emoji(emoji['money'])}"

    all_active_players[str(current_game_data["message"].id)][str(ctx.author.id)]["bet"] = player_raise
    all_active_players[str(current_game_data["message"].id)][str(ctx.author.id)]["action"] = "reraise"

    if player_raise >= user.balance:
        action = f"{ctx.author} пошёл в all-in!"
        player_raise = user.balance
        all_active_players[str(current_game_data["message"].id)][str(ctx.author.id)]["action"] = "all-in"

    user.balance -= player_raise

    changed_players_amount = await get_all_next_players(new_min_bet, active_players)
    next_player_id, next_player = await get_next_player(new_min_bet, active_players, guild)
    new_game_data = {
        "next_player": next_player,
        "next_player_id": next_player_id,
        "max_player_id": current_game_data["max_player_id"] + changed_players_amount,
        "new_pot": current_game_data["pot"] + player_raise,
        "new_min_bet": new_min_bet,
        "last_action": action
    }

    db_sess.commit()
    await commit_changes(all_active_players, "game_data/active_players.json")
    await commit_game_changes(current_game_data["message"], new_game_data, guild)


@client.command()
async def leave(ctx):
    await ctx.channel.set_permissions(ctx.author, send_messages=False, read_messages=False)


async def poker_win(ctx):
    pass


async def get_all_next_players(current_bet, members_data):
    next_players = []
    for member_data in members_data.values():
        if member_data["bet"] < current_bet and member_data["action"] != "all-in":
            next_players.append("player")

    return len(next_players)


async def get_next_player(current_bet, members_data, guild):
    next_player = None
    next_player_id = -1
    for member_id, member_data in members_data.items():
        if member_data["bet"] < current_bet and member_data["action"] != "all-in":
            next_player_id = list(members_data.keys()).index(next_player_id) + 1
            next_player = guild.get_member(member_id)
            break

    return next_player_id, next_player


async def get_formatted_players(members, guild_id, value_emoji):
    members_text = [[], []]
    member_pos = 1
    column = 0
    for member in members:
        balance = db_sess.query(User).filter(User.id == f"{member.id}-{guild_id}").first().balance
        members_text[column].append(f"**{member_pos}.\t{member.name}:**\n"
                                    f"Баланс:\t{balance} {value_emoji}")
        if member_pos == len(members) % 2 + len(members) // 2:
            column += 1
        member_pos += 1

    return members_text


async def start_new_round(round_num, message):
    deck = DeckOfCards()
    deck.cards = json.load(open("game_data/active_card_decks.json", encoding="utf8"))[str(message.id)]
    embed = message.embeds[0]

    amount_to_take = 3 if round_num == 2 else 1
    text_cards = []
    for card_info in await deck.take(amount_to_take):
        value, suit = card_info.split(" - ")
        text_cards.append(f"{value} {client.get_emoji(playing_cards_emoji[suit])}")
    text_cards = "\n".join(text_cards)

    embed.set_field_at(6, name="\u200b",
                       value=f"**Открытые карты:**\n"
                             f"{text_cards}")

    await message.edit(embed=embed)


async def commit_game_changes(message, data, guild):
    value_emoji = client.get_emoji(emoji["money"])
    embed = message.embeds[0]

    old_third_field_value = "\n".join(embed.fields[3].value.split("\n")[:4])
    embed.set_field_at(3, name="\u200b",
                       value=f"{old_third_field_value}\n"
                             f"{data['next_player_id']}.\t{data['next_player']}\n"
                             f"Ход раунда: {data['next_player_id']} из {data['max_player_id']}",
                       inline=True)

    embed.set_field_at(5, name="\u200b",
                       value=f"**Общий куш:**\n"
                             f"{data['new_pot']} {value_emoji}\n\n"
                             f"**Минимальная ставка:**\n"
                             f"{data['new_min_bet']} {value_emoji}")

    if "вышел из игры" in data["last_action"]:
        all_active_members = json.load(open("game_data/active_players.json", encoding="utf8"))
        members = [guild.get_member(member_id)
                   for member_id in list(all_active_members[str(message.id)].keys())]
        members_text = await get_formatted_players(members, guild.id, value_emoji)

        embed.set_field_at(0, name="\u200b", value="\n\n".join(members_text[0]), inline=True)
        embed.set_field_at(1, name="\u200b", value="\u200b", inline=True)
        embed.set_field_at(2, name="\u200b", value="\n\n".join(members_text[1]), inline=True)
    elif data["last_action"] != "":
        embed.set_field_at(7, name="\u200b",
                           value=f"**Последнее действие:**\n"
                                 f"{data['last_action']}")

    await message.edit(embed=embed)

    if not data["next_player"]:
        opened_cards = embed.fields[6].value.split("\n")[1:]
        round_num = len(opened_cards) if len(opened_cards) > 1 else len(opened_cards) + 1

        await start_new_round(round_num, message)


async def get_current_game_data(ctx):
    pins = await ctx.channel.pins()
    current_game_message = None
    for pin_message in pins:
        if pin_message.embeds and "Партия в покер в процессе" == pin_message.embeds[0].title:
            current_game_message = pin_message
            break

    if not current_game_message:
        print("Нет активных игр")
        return

    current_game_data = {}

    embed = current_game_message.embeds[0]

    raw_bet_data = embed.fields[5].value.split("\n")
    round_info = embed.fields[3].value.split("\n")[5].split()

    current_player_line = embed.fields[3].value.split("\n")[4]
    current_player_name, current_player_desc = " ".join(current_player_line.split()[1:]).split("#")

    current_game_data["message"] = current_game_message

    current_game_data["pot"] = int(raw_bet_data[1].split()[0])
    current_game_data["min_bet"] = int(raw_bet_data[4].split()[0])

    current_game_data["current_player"] = get(ctx.guild.members,
                                              name=current_player_name,
                                              discriminator=current_player_desc)

    current_game_data["current_player_id"] = int(round_info[2])
    current_game_data["max_player_id"] = int(round_info[4])

    return current_game_data


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

    if get(guild.roles, name="Игрок") not in member.roles:
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
    guild = ctx.guild
    author = ctx.author

    if city.name not in ["Тополис", "Браифаст", "Джадифф"]:
        raise IncorrectCityName(f"- {city.name} - не является названием существующего города!")
    if city in author.roles:
        raise IncorrectCityName(f"- Вы и так находитесь в {city.name}!")

    user = db_sess.query(User).filter(User.id == f"{author.id}-{guild.id}").first()

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
    embed = discord.Embed(title=f"⮮ __**{user.name}:**__", color=4017407)

    embed.add_field(name='**Баланс:**', value=f"*```md\n# {user.balance} Gaudium```*", inline=False)
    text1 = f"*```md\n" \
            f"# Раса ➢ {user.nation}\n" \
            f"# Происхождение ➢ {user.origin}```*"
    embed.add_field(name='**Сведения:**', value=text1, inline=False)
    text2 = f"*```md\n" \
            f"# Здоровье ➢ {user.health}\n" \
            f"# Сила ➢ {user.strength}\n"\
            f"# Интелект ➢ {user.intelligence}\n" \
            f"# Маторика ➢ {user.dexterity}\n" \
            f"# Скорость ➢ {user.speed}```*"
    embed.add_field(name='**Характеристики:**', value=text2, inline=False)
    embed.add_field(name='**Свободных очков навыка:**', value=f"*```md\n# {user.skill_points}```*", inline=False)

    embed.set_thumbnail(url=author.avatar_url)
    embed.set_footer(text=f"Никнейм Discord: {author.name}")

    await ctx.send(embed=embed)


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


# @fold.error
# async def fold_error(ctx, error):
#     await throw_error(ctx, error)


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

    embed = discord.Embed(title="⮮ __**БОТ СТОЛКНУЛСЯ С ОШИБКОЙ:**__", color=0xed4337)
    embed.add_field(name="**Причина:**",
                    value=f"```diff\n{text}\n```",
                    inline=False)
    await ctx.send(embed=embed)


"""
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- ЗАПУСК БОТА -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
"""

DiscordComponents(client)
client.run(TOKEN)
