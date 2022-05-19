import asyncio
import random
from pafy import new as make_new_video
from datetime import datetime

from nextcord.ext import commands
from nextcord import Interaction, FFmpegPCMAudio
from nextcord.utils import get

from constants import *
from cogs.trade import add_item


FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -stream_loop -1',
    'options': '-vn'
}
VIDEO_LINK = "https://www.youtube.com/watch?v=z_HWtzUHm6s&t=1s"

NATION_TITLES = ['Северяне', 'Южане', 'Техно-гики']
ORIGIN_TITLES = ['Богатая семья', 'Обычная семья', 'Бедная семья']

GAME_ROLES_COLORS = {
    "Игрок": 44444,
    "Тополис": 16777215,
    "Браифаст": 16777215,
    "Джадифф": 16777215
}
OBJECTS = json.load(open("json_data/objects.json", encoding="utf8"))

TIME_STORE_UPDATE = "18:00"
STORE_TYPES = json.load(open("json_data/store_types.json", encoding="utf8"))


class NationButton(nextcord.ui.Button):
    def __init__(self, bot, title):
        super().__init__(style=nextcord.ButtonStyle.gray, emoji=bot.get_emoji(EMOJIS_ID[title]))
        self.title = title

    async def callback(self, interaction: Interaction):
        user_id = f"{interaction.user.id}-{interaction.guild.id}"

        user = db_sess.query(User).filter(User.id == user_id).first()
        user.nation = self.title

        await interaction.send(f"*Теперь вы пренадлежите расе **{self.title}**!* [Это сообщение можно удалить]")
        db_sess.commit()


class NationView(nextcord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)

        for title in NATION_TITLES:
            self.add_item(NationButton(bot, title))


class OriginButton(nextcord.ui.Button):
    def __init__(self, bot, title):
        super().__init__(style=nextcord.ButtonStyle.gray, emoji=bot.get_emoji(EMOJIS_ID[title]))
        self.title = title

    async def callback(self, interaction: Interaction):
        user = db_sess.query(User).filter(User.id == f"{interaction.user.id}-{interaction.guild.id}").first()
        user.origin = self.title

        await interaction.send(f"*Теперь вы из \"**{self.title}**\"!* [Это сообщение можно удалить]")
        db_sess.commit()


class OriginView(nextcord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)

        for title in ORIGIN_TITLES:
            self.add_item(NationButton(bot, title))


class ShopButton(nextcord.ui.Button):
    def __init__(self, bot, item_name):
        super().__init__(
            style=nextcord.ButtonStyle.gray,
            label=f"Купить {item_name}"
        )
        self.item_name = item_name
        self.bot = bot

    async def callback(self, interaction: Interaction):
        user = interaction.user
        guild = interaction.guild

        value_emoji = self.bot.get_emoji(EMOJIS_ID["Валюта"])
        item = db_sess.query(Items).filter(Items.name == self.item_name).first()
        user = db_sess.query(User).filter(User.id == f"{user.id}-{guild.id}").first()

        if user.balance < item.price:
            await interaction.send(f"***Вам не хватило денег**! Ваш баланс: {user.balance} {value_emoji}* "
                                   f"[Это сообщение можно удалить]")
        else:
            user.balance -= item.price
            await add_item(guild, user.id, self.item_name)
            await interaction.send(f"*Вы приобрели **{self.item_name}**! Ваш баланс: {user.balance} {value_emoji}* "
                                   f"[Это сообщение можно удалить]")

        db_sess.commit()


class ShopView(nextcord.ui.View):
    def __init__(self, bot, items):
        super().__init__()

        for item in items:
            self.add_item(ShopButton(bot, item.name))


class ServerSetupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ФУНКЦИЯ, обновляющая магазин
    async def store_update(self, guild):
        store_channel = get(guild.channels, name="🛒магазин")
        if store_channel:
            # Удаление сообщений
            await store_channel.purge(limit=None)

            # Список всех предметов
            all_items = db_sess.query(Items).all()
            for item_type in STORE_TYPES:
                # Выбор случайного набора предметов определённого типа
                items = list(filter(lambda x: x.type in item_type.keys(), all_items.copy()))
                random.shuffle(items)
                items = items[:random.randint(4, 6)]

                # Embed сообщения
                embed = nextcord.Embed(title=f"⮮ __**{item_type['NAME']}:**__", color=0xf1c40f)
                for item in items:
                    embed.add_field(
                        name=f"**{item.name}:**",
                        value=f"➢ **Цена:** {item.price} {self.bot.get_emoji(EMOJIS_ID['Валюта'])}"
                              f"```fix\nОписание: {item.description} Тип: {item_type[item.type]}```", inline=False
                    )

                # Создание кнопок для сообщение
                shop_view = ShopView(self.bot, items)

                # Отправка сообщения
                await store_channel.send(embed=embed, view=shop_view)

    # ФУНКЦИЯ, проверяющая нужно ли обновить магазин
    async def store_update_cycle(self):
        while True:
            if datetime.now().strftime("%H:%M") == TIME_STORE_UPDATE:
                for guild in self.bot.guilds:
                    await self.store_update(guild)
            await asyncio.sleep(60)

    # ФУНКЦИЯ, подключение к каналу "🎶Главная тема" на всех серверах
    async def channel_connection(self):
        for guild in self.bot.guilds:
            voice_channel = get(guild.voice_channels, name="🎶Главная тема")
            if voice_channel:
                try:
                    # Подключение к каналу
                    voice = await voice_channel.connect()
                    # Включение музыки
                    video = make_new_video(VIDEO_LINK)
                    audio = video.getbestaudio().url
                    voice.play(FFmpegPCMAudio(audio, **FFMPEG_OPTIONS, executable="ffmpeg/bin/ffmpeg.exe"))
                except Exception as e:
                    print(e)

    # ФУНКЦИЯ, отправляющаю сообщение в чат регистрации
    async def send_registration_msg(self, channel):
        await channel.send(f"**В этом чате вы должны создать своего персонажа.**\n"
                           f"*Подходите к этому вопросу с умом!*")

        # ======= ВЫБОР РАСЫ
        nation_embed = nextcord.Embed(title='⮮ __**Выбор расы:**__', color=44444)
        nation_embed.add_field(
            name='**Важно:**',
            value='*```yaml\n'
                  '➢ От расы зависят некоторые характеристики.\n'
                  '➢ Пока вы не завершите создание профиля вы можете перевыбирать расу.```*',
            inline=False)

        # ======= ВЫБОР ПРОИСХОЖДЕНИЯ
        origin_embed = nextcord.Embed(title='⮮ __**Выбор происхождения:**__', color=44444)
        origin_embed.add_field(
            name='**Важно:**',
            value='*```yaml\n'
                  '➢ От происхождения зависят некоторые характеристики.\n'
                  '➢ Пока вы не завершите создание профиля вы можете перевыбирать происхождение.```*',
            inline=False
        )

        # ======= СОЗДАНИЕ ИМЕНИ
        name_embed = nextcord.Embed(title='⮮ __**Ваше имя:**__', color=44444)
        name_embed.add_field(
            name='**Важно:**',
            value='*```yaml\n'
                  '➢ Желаемое вами имя напишите в данный чат с помощью команды: "/name".\n'
                  '➢ Имя не влияет на характеристики, при написании команды напишите имя маленькими буквами.\n'
                  '➢ Вводите имя с умом так как его можно будет изменить только через админа.\n'
                  '➢ После написания имени вы завершите создание профиля.```*',
            inline=False
        )

        await channel.send(embed=nation_embed, view=NationView(self.bot))
        await channel.send(embed=origin_embed, view=OriginView(self.bot))
        await channel.send(embed=name_embed)

    # ФУНКЦИЯ, отправляющаю сообщение в чат информации
    @staticmethod
    async def send_information_msg(channel):
        # ======= История
        text = '*```yaml\n' \
               '\tОколо века назад человечество смогло покинуть Землю и освоить Марс, ' \
               'на нём люди нашли руду под названием Экзорий. Люди тщательно изучали Экзорий, ' \
               'и открыли для себя много разных свойств этой руды, в результате многих экспериментов ' \
               'люди смогли извлекать из этой руды много энергии с огромной мощью. В ходе таких ' \
               'открытий люди смогли быстро развить технологии и освоить космос намного лучше, ' \
               'человечество стало путешествовать и колонизировать различные планеты в различных ' \
               'звёздных системах.\n\n' \
               '\tЗемля в своё время, к сожалению стала деградировать, из за экспериментов ' \
               'которые проводили на Земле и людей отвергающих новые технологии, родная планета ' \
               'человечества через некоторое время стала скверным местом. На Землю стали отправлять ' \
               'неугодных людей, которые совершали какие либо преступление. Уже несколько поколений люди ' \
               'с планеты Земля живут в ужасном мире этой планеты. Вы родились на Земле, и вам ' \
               'предстоит на ней выжить.```*'
        history_embed = nextcord.Embed(title='⮮ __**История:**__', color=44444)
        history_embed.add_field(name='\u200b', value=text, inline=False)

        # ======= Инфо
        embed = nextcord.Embed(title='⮮ __**Дополнительная информация:**__', color=44444)
        embed.add_field(
            name='\u200b',
            value='*```yaml\n'
                  '➢ Для того что бы узнать команды, напишите в чате "/", вам предоставится '
                  'список команд с их описаниями.\n'
                  '➢ Основная валюта игры: "Gaudium".\n'
                  '➢ Если у вас возникла ошибка обращайтесь к администрации.```*', inline=False)

        await channel.send(embed=history_embed)
        await channel.send(embed=embed)

    # ФУНКЦИЯ, записывающая всех с сервера в базу данных
    @staticmethod
    async def write_db(guild):
        check_write_db = False
        for member in guild.members:
            user_id = f"{member.id}-{guild.id}"
            if not member.bot and not db_sess.query(User).filter(User.id == user_id).first():
                user = User()
                user.id = user_id
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
                user.equipped_inventory = ''

                db_sess.add(user)
                check_write_db = True
        db_sess.commit()
        return check_write_db

    # ФУНКЦИЯ, удаляющая всех с сервера из базы данных
    @staticmethod
    async def delete_db(guild):
        for member in guild.members:
            user = db_sess.query(User).filter(User.id == f"{member.id}-{guild.id}").first()
            if not member.bot and user:
                db_sess.delete(user)
        db_sess.commit()

    # ФУНКЦИЯ, создающая категории
    @staticmethod
    async def create_category(guild, title):
        return await guild.create_category(title)

    # ФУНКЦИЯ, создающая чаты
    @staticmethod
    async def create_channel(guild, channel_info, category, title, roles_for_permss):
        kind, allow_messaging, pos = channel_info
        channel = None
        # Создание чата
        if not get(guild.channels, name=title):
            channel = await guild.create_text_channel(title, category=category, position=pos)
            # Настройка доступа к чату
            if kind != 'all':
                for _name, role in roles_for_permss.items():
                    await channel.set_permissions(
                        role,
                        send_messages=allow_messaging,
                        read_messages=kind == _name
                    )

        return channel

    # КОМАНДА, настраивающая сервер
    @commands.command()
    @commands.has_guild_permissions(administrator=True)
    async def implement(self, interaction: Interaction):
        await interaction.message.delete()
        guild = interaction.guild
        check_implement = False

        # Создание ролей
        for _name, color in GAME_ROLES_COLORS.items():
            if not get(guild.roles, name=_name):
                await guild.create_role(name=_name, color=color)
                await interaction.send(f":white_check_mark: *Роль {_name} создана.*")
                check_implement = True

        roles_for_permss = {
            "non-game": guild.default_role,
            "game": get(guild.roles, name="Игрок"),
            "city_topolis": get(guild.roles, name="Тополис"),
            "city_braifast": get(guild.roles, name="Браифаст"),
            "city_jadiff": get(guild.roles, name="Джадифф")
        }

        # Создание чатов и категорий
        for category, channels in OBJECTS.items():
            # Создание категории
            category_object = get(guild.categories, name=category)
            if not category_object:
                category_object = await self.create_category(guild, category)
                check_implement = True
                await interaction.send(f":white_check_mark: *Категория {category} создана.*")

            # Создание чатов
            for channel_name in channels.keys():
                channel = await self.create_channel(
                    guild,
                    channels[channel_name].values(),
                    category_object,
                    channel_name,
                    roles_for_permss
                )
                if channel:
                    check_implement = True
                    if channel.name == "🚪создание-персонажа":
                        await self.send_registration_msg(get(guild.channels, name="🚪создание-персонажа"))
                    if channel.name == "📜информация":
                        await self.send_information_msg(get(guild.channels, name="📜информация"))
                    if channel.name == "🛒магазин":
                        pass

            # Добавление чатов в категорию (сделано для повторного /implement)
            for channel in channels.keys():
                await get(guild.channels, name=channel).edit(
                    category=category_object,
                    position=channels[channel]["position"]
                )

        # Создание канала для прослушивания музыки
        name_voice = "🎶Главная тема"
        if not get(guild.voice_channels, name=name_voice):
            channel = await guild.create_voice_channel(name_voice,
                                                       category=get(guild.categories, name="ОБЩЕЕ"), position=4)
            await channel.set_permissions(roles_for_permss["non-game"], speak=False, view_channel=False)
            await channel.set_permissions(roles_for_permss["game"], speak=False, view_channel=True)
            check_implement = True

        # Заполнение базы данных
        if await self.write_db(guild):
            await interaction.send(":white_check_mark: *База данных заполнена.*")
            check_implement = True

        # Создание магазина
        await self.store_update(guild)

        # Подключение к каналу "🎶Главная тема"
        await self.channel_connection()

        # Уведомление
        if check_implement:
            await interaction.send(":white_check_mark: **Готово!**")
        else:
            await interaction.send(":x: **Первоначальная настройка уже была произведена!**")

    # КОМАНДА, удаляющая настройку сервера
    @commands.command()
    @commands.has_guild_permissions(administrator=True)
    async def reset(self, interaction: Interaction):
        await interaction.message.delete()
        guild = interaction.guild

        # Удаление чатов категорий и тд
        try:
            for category, channels in OBJECTS.items():
                await get(guild.categories, name=category).delete()
                for channel in channels.keys():
                    await get(guild.channels, name=channel).delete()
            for role in GAME_ROLES_COLORS:
                await get(guild.roles, name=role).delete()
        except AttributeError:
            pass

        await get(guild.voice_channels, name="🎶Главная тема").delete()

        # Удаление базы данных
        await self.delete_db(guild)

        # Уведомление
        await interaction.send(":white_check_mark: **Готово!**")

    # КОМАНДА, удаляющая всех с сервера из базы данных
    @commands.command()
    @commands.has_guild_permissions(administrator=True)
    async def delete_users(self, interaction: Interaction):
        await interaction.message.delete()
        guild = interaction.guild
        chek_delete_db = False

        for member in guild.members:
            user = db_sess.query(User).filter(User.id == f"{member.id}-{guild.id}").first()
            if not member.bot and user:
                db_sess.delete(user)
                chek_delete_db = True
        db_sess.commit()

        # Уведомление
        if chek_delete_db:
            await interaction.send(":white_check_mark: **Готово!**")
        else:
            await interaction.send(":x: **Пользователей нет в базе данных!**")


def setup(bot):
    bot.add_cog(ServerSetupCog(bot))
