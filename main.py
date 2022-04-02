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
    guild = interaction.guild
    decision_type = interaction.component.label
    member = interaction.user
    id_user = f"{member.id}{guild.id}"
    if decision_type in group_lbl_button_nation:
        user = db_sess.query(User).filter(User.id == id_user).first()
        user.nation = decision_type
        await interaction.send(f"*Теперь вы пренадлежите расе **{decision_type}**!* [Это сообщение можно удалить]")
    if decision_type in group_lbl_button_origin:
        user = db_sess.query(User).filter(User.id == id_user).first()
        user.origin = decision_type
        await interaction.send(f"*Теперь вы из \"**{decision_type}**\"!* [Это сообщение можно удалить]")
    db_sess.commit()


# ФУНКЦИЯ, создающая категории
async def create_category(guild, title):
    return await guild.create_category(title)


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


# ФУНКЦИЯ, отправляющаю сообщение в чат информации
async def send_information_msg(channel):
    # ======= История
    text = '*```yaml\n' \
           '  Около века назад человечество смогло покинуть Землю и освоить Марс, на нём люди нашли руду под' \
           'названием Экзорий. Люди тщательно изучали Экзорий, и открыли для себя много различных свойств этой руды, в' \
           'результате многих экспериментов люди смогли извлекать из этой руды много энергии с огромной мощью. В ходе' \
           'таких открытий люди смогли быстро развить технологии и освоить космос намного лучше, человечество стало' \
           'путешествовать и колонизировать различные планеты в различных звёздных системах.' \
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


# ФУНКЦИЯ, создающая чаты
async def create_channel(guild, channel_info, category, title, roles_for_permss):
    kind, allow_messaging, pos = channel_info
    channel = None
    if not get(guild.channels, name=title):
        channel = await guild.create_text_channel(title, category=category, position=pos)

        if kind != 'all':
            for name, role in roles_for_permss.items():
                await channel.set_permissions(role,
                                              send_messages=allow_messaging,
                                              read_messages=kind == name)
    return channel


# ФУНКЦИЯ, записывающая всех с сервера в базу данных
async def write_db(guild):
    chek_write_db = False
    for member in guild.members:
        id_user = f"{member.id}{guild.id}"
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
        user = db_sess.query(User).filter(User.id == f"{member.id}{guild.id}").first()
        if not member.bot and user:
            db_sess.delete(user)
    db_sess.commit()


# КОМАНДА, удаляющая всех с сервера из базы данных
@client.command()
@commands.has_guild_permissions(administrator=True)
async def delete_users(ctx):
    await ctx.message.delete()
    guild = ctx.guild
    chek_delete_db = False
    for member in guild.members:
        user = db_sess.query(User).filter(User.id == f"{member.id}{guild.id}").first()
        if not member.bot and user:
            db_sess.delete(user)
            chek_delete_db = True
    db_sess.commit()
    # Уведомление
    if chek_delete_db:
        await ctx.send(":white_check_mark: **Готово!**")
    else:
        await ctx.send(":x: **Пользователей нет в базе данных!**")


# КОМАНДА, настраивающая сервер
@client.command()
@commands.has_guild_permissions(administrator=True)
async def implement(ctx):
    await ctx.message.delete()
    guild = ctx.guild
    chek_implement = False
    color1 = 44444
    color2 = 16777215
    # Создание ролей
    setting_roles = [("Игрок", color1), ("Тополис", color2), ("Браифаст", color2), ("Джадифф", color2)]
    for name, color in setting_roles:
        if not get(guild.roles, name=name):
            await guild.create_role(name=name, color=color)
            await ctx.send(f":white_check_mark: *Роль {name} создана.*")
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
            await ctx.send(f":white_check_mark: *Категория {category} создана.*")
            chek_implement = True
        # Создание чатов
        for channel in channels.keys():
            channel = await create_channel(guild, channels[channel].values(), _category, channel, roles_for_permss)
            if channel:
                await ctx.send(f":white_check_mark: *Чат {channel.name} создан.*")
                chek_implement = True
                name = "создание-персонажа"
                if channel.name == name:
                    await send_registration_msg(get(guild.channels, name=name))
                name = "информация"
                if channel.name == name:
                    await send_information_msg(get(guild.channels, name=name))
        # Добавление чатов в категорию (сделано для повторного /implement)
        for channel in channels.keys():
            await get(guild.channels, name=channel).edit(category=_category, position=channels[channel]["position"])

    # Заполнение базы данных
    if await write_db(guild):
        await ctx.send(":white_check_mark: *База данных заполнена.*")
        chek_implement = True

    # Уведомление
    if chek_implement:
        await ctx.send(":white_check_mark: **Готово!**")
    else:
        await ctx.send(":x: **Первоначальная настройка уже была произведена!**")


# КОМАНДА, удаляющая всё не нужное
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

    # Удаление базы данных
    await delete_db(guild)

    # Уведомление
    await ctx.send(":white_check_mark: **Готово!**")


# КОМАНДА, добавляющая ник и создающая профиль
@client.command()
async def name(ctx, *args):
    await ctx.message.delete()
    guild = ctx.guild
    member = ctx.author

    # Проверка в нужном ли чате используется команда
    name_channel = "создание-персонажа"
    if ctx.channel.id != get(guild.channels, name=name_channel).id:
        await member.send(f":x: **Данную команду вы можете использовать только в чате \"{name_channel}\".**")
        return
    # Проверка на присутствие самого имени
    if not args:
        await member.send(f":x: **Введите имя через пробел после команды, имя не может отсутствовать.**")
        return

    _name = ' '.join(args)
    user = db_sess.query(User).filter(User.id == f"{member.id}{guild.id}").first()

    for role in member.roles:
        if role.name == 'Игрок':
            await member.send(':x: **Вы не можете поменять своё имя!** *Для этого обратитесь к администрации.*')
            return
    if user.nation == '-1' or user.origin == '-1':
        await member.send(':x: **Вы не можете создать профиль не выбрав расу или происхождение!**')
        return
    await member.send(':white_check_mark: **Вы успешно создали своего персонажа, удачной игры!**')

    user.name = _name
    db_sess.commit()
    # Добавляется роль @Игрок
    role = get(guild.roles, name="Игрок")
    await member.add_roles(role)


# КОМАНДА, добавляющая предмет
# @slash.slash(
#     name="add_item",
#     description="Отправить предложение обмена другому игроку",
#     options=[{"name": "item", "description": "предмет", "type": 3, "required": True}],
#     guild_ids=test_servers_id
# )
async def add_item(ctx, item):
    guild = ctx.guild
    player = ctx.author
    db_sess.query(User).filter(User.id == f"{player.id}{guild.id}").first().inventory += f"{item};"
    db_sess.commit()
    await ctx.send("Done")


async def get_inventory(player_id, guild):
    user = db_sess.query(User).filter(User.id == f"{player_id}{guild.id}").first()
    player_inventory = {}
    for item in user.inventory.split(";"):
        player_inventory[item] = player_inventory.get(item, 0) + 1
    db_sess.commit()
    return player_inventory


# КОМАНДА, трейд
@slash.slash(
    name="trade",
    description="Отправить предложение обмена другому игроку",
    options=[{"name": "member", "description": "пользователь", "type": 6, "required": True}],
    guild_ids=test_servers_id
)
# @commands.has_role("Игрок")
async def trade(ctx, member):
    guild = ctx.guild
    player = ctx.author
    if player == member or member.bot:
        await throw_error(ctx, 100)
        return

    player_inventory = await get_inventory(player.id, guild)
    member_inventory = await get_inventory(member.id, guild)

    emb = discord.Embed(title="**Ваш инвентарь**", color=0xFFFFF0)
    await ctx.send(f"Выберете предметы из своего инвентаря и из инвентаря {member.mention}")
    msg = await ctx.channel.send("dfsdf")
    await msg.add_reaction("1️⃣")
    # msg = ctx.message
    # await msg.add_reaction(":zero:")
    # await msg.add_reaction(":one:")
    # await msg.add_reaction(":two:")
    # await msg.add_reaction(":three:")
    # await msg.add_reaction(":four:")
    # await msg.add_reaction(":five:")
    # await msg.add_reaction(":six:")
    # await msg.add_reaction(":seven:")
    # await msg.add_reaction(":eight:")
    # await msg.add_reaction(":nine:")
    # await msg.add_reaction(":ten:")
    # msg.add_reaction("1")

    # emb = discord.Embed(title=f"**Инвентарь игрока {member.name}**", color=0xdf213)
    # buttons = [[]]
    #
    # for item in player_inventory:
    #     buttons[0].append(Button(style=ButtonStyle.gray, label=f"{item} x{player_inventory[item]}"))
    # await ctx.channel.send(embed=emb, components=buttons)


# КОМАНДА, открывающая инвентарь
@slash.slash(
    name="open_inventory",
    description="Открыть инвентарь персонажа",
    guild_ids=test_servers_id
)
@commands.has_role("Игрок")
async def open_inventory(ctx):
    guild = ctx.guild
    value_emoji = client.get_emoji(emoji["money"])
    player_inventory = await get_inventory(ctx.author.id, guild)

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
