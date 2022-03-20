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
            await ctx.send(f":x: Чат регистрации уже создан.")
            return

    channel = await guild.create_text_channel(name)

    await channel.send(f"**В этом чате вы должны создать своего персонажа.** *подходите к этому вопросу с умом!*")

    # ======= ВЫБОР РАСЫ
    text = '*```yaml\n➢ От расы зависят некоторые характеристики.\n➢ [Дописать что то ещё].```*'
    emb = discord.Embed(title='⮮ __**Выбор расы:**__', color=44444)
    emb.add_field(name='**Важно:**', value=text, inline=False)

    emoji1 = client.get_emoji(954886438233710664)
    # discord.utils.get(guild.emojis, name="north")
    emoji2 = client.get_emoji(954886483817426954)
    # discord.utils.get(guild.emojis, name="south")
    emoji3 = client.get_emoji(954886667557285908)
    # discord.utils.get(guild.emojis, name="techno")

    # for guild in client.guilds:
    #

    await channel.send(
        embed=emb,
        components=[
            [Button(style=ButtonStyle.green, label="Северяне", emoji=emoji1),
             Button(style=ButtonStyle.green, label="Южнане", emoji=emoji2),
             Button(style=ButtonStyle.green, label="Техно-гики", emoji=emoji3)]
        ]
    )
    # ======= ВЫБОР ПРОИСХОЖДЕНИЯ
    text = '*```yaml\n➢ От происхождения зависят некоторые характеристики.\n➢ [Дописать что то ещё].```*'
    emb = discord.Embed(title='⮮ __**Выбор происхождения:**__', color=44444)
    emb.add_field(name='**Важно:**', value=text, inline=False)

    emoji1 = client.get_emoji(954894281972277319)
    # discord.utils.get(guild.emojis, name="rich")
    emoji2 = client.get_emoji(954894246303920149)
    # discord.utils.get(guild.emojis, name="norm")
    emoji3 = client.get_emoji(954894194537811988)
    # discord.utils.get(guild.emojis, name="poor")

    # for guild in client.guilds:
    #     emoji1 = discord.utils.get(guild.emojis, name="rich")
    #     emoji2 = discord.utils.get(guild.emojis, name="norm")
    #     emoji3 = discord.utils.get(guild.emojis, name="poor")

    await channel.send(
        embed=emb,
        components=[
            [Button(style=ButtonStyle.green, label="Богатая семья", emoji=emoji1),
             Button(style=ButtonStyle.green, label="Нормальная семья", emoji=emoji2),
             Button(style=ButtonStyle.green, label="Бедность", emoji=emoji3)]
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
client.run(TOKEN)
