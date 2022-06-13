import asyncio
import random
from datetime import datetime

from general_imports import *

# TODO: оптимизировать код
# TODO: улучшить дизайн команд
# TODO: убрать ненужные ephemeral из сообщений
# TODO: добавить локализацию выводов для англ и рус языков
# TODO: избавиться от багов

# TODO: добавить команду для более детальной настройки бота
# TODO: Доработать систему регистрации
# TODO: Сделать логику магазинов более удобной
# TODO: Засунить вышеперечисленные команды в отдельный файл

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -stream_loop -1',
    'options': '-vn'
}
VIDEO_LINK = "https://www.youtube.com/watch?v=z_HWtzUHm6s&t=1s"

NATION_TITLES = ['Северяне', 'Южане', 'Техно-гики']
ORIGIN_TITLES = ['Богатая семья', 'Обычная семья', 'Бедная семья']

GAME_ROLES_COLORS = {
    "Игрок": 0xAF4425,
    "Тополис": 0xFFFFFF,
    "Браифаст": 0xFFFFFF,
    "Джадифф": 0xFFFFFF
}
OBJECTS = json.load(open("json_data/objects.json", encoding="utf8"))

TIME_STORE_UPDATE = "18:00"
STORE_TYPES = json.load(open("json_data/store_types.json", encoding="utf8"))


# TODO: стоит это убрать, пока что не работает как хотелось
# class RegistrationModal(nextcord.ui.Modal):
#     def __init__(self):
#         super().__init__(
#             "Создания персонажа",
#             timeout=5 * 60
#         )
#
#         # self.nation_select = nextcord.ui.Select(
#         #     placeholder="Выберите расу Вашего персонажа",
#         #     options=[
#         #         nextcord.SelectOption(
#         #             label="Северяне",
#         #             description="В чём их бафы"
#         #         ),
#         #         nextcord.SelectOption(
#         #             label="Южане",
#         #             description="В чём их бафы"
#         #         ),
#         #         nextcord.SelectOption(
#         #             label="Техно-гики",
#         #             description="В чём их бафы"
#         #         )
#         #     ]
#         # )
#         # self.add_item(self.nation_select)
#         #
#         # self.origin_select = nextcord.ui.Select(
#         #     placeholder="Выберите расу Вашего персонажа",
#         #     options=[
#         #         nextcord.SelectOption(
#         #             label="Богатая семья",
#         #             description="В чём их бафы"
#         #         ),
#         #         nextcord.SelectOption(
#         #             label="Обычная семья",
#         #             description="В чём их бафы"
#         #         ),
#         #         nextcord.SelectOption(
#         #             label="Бедная семья",
#         #             description="В чём их бафы"
#         #         )
#         #     ]
#         # )
#         # self.add_item(self.origin_select)
#
#         self.name_input = nextcord.ui.TextInput(
#             label="Введите имя Вашего персонажа",
#             min_length=3,
#             max_length=15
#         )
#         self.add_item(self.name_input)
#
#     # async def callback(self, interaction: nextcord.Interaction) -> None:
#     #     await interaction.send(f"{self.nation_select.values}, {self.origin_select.values}, {self.name_input.value}")
#
#
# TODO: подразобрать этот блок кода
# class NationButton(nextcord.ui.Button):
#     def __init__(self, title: str):
#         super().__init__(style=nextcord.ButtonStyle.gray, emoji=EMOJIS[title])
#         self.title = title
#
#     async def callback(self, interaction: Interaction):
#         user_id = f"{interaction.user.id}-{interaction.guild.id}"
#
#         user = DB_SESSION.query(User).filter(User.id == user_id).first()
#         user.nation = self.title
#
#         await interaction.send(f"*Теперь вы пренадлежите расе **{self.title}**!* [Это сообщение можно удалить]")
#         DB_SESSION.commit()
#
#
# class NationView(nextcord.ui.View):
#     def __init__(self):
#         super().__init__(timeout=None)
#
#         for title in NATION_TITLES:
#             self.add_item(NationButton(title))
#
#
# class OriginButton(nextcord.ui.Button):
#     def __init__(self, title: str):
#         super().__init__(style=nextcord.ButtonStyle.gray, emoji=EMOJIS[title])
#         self.title = title
#
#     async def callback(self, interaction: Interaction):
#         user = DB_SESSION.query(User).filter(User.id == f"{interaction.user.id}-{interaction.guild.id}").first()
#         user.origin = self.title
#
#         await interaction.send(f"*Теперь вы из \"**{self.title}**\"!* [Это сообщение можно удалить]")
#         DB_SESSION.commit()
#
#
# class OriginView(nextcord.ui.View):
#     def __init__(self):
#         super().__init__(timeout=None)
#
#         for title in ORIGIN_TITLES:
#             self.add_item(NationButton(title))
#
#
# class ShopButton(nextcord.ui.Button):
#     def __init__(self, bot: commands.Bot, item_name):
#         super().__init__(
#             style=nextcord.ButtonStyle.gray,
#             label=f"Купить {item_name}"
#         )
#         self.item_name = item_name
#
#     async def callback(self, interaction: Interaction):
#         user = interaction.user
#         guild = interaction.guild
#
#         value_emoji = EMOJIS["Валюта"]
#         item = DB_SESSION.query(Items).filter(Items.name == self.item_name).first()
#         user = DB_SESSION.query(User).filter(User.id == f"{user.id}-{guild.id}").first()
#
#         if user.balance < item.price:
#             await interaction.send(f"***Вам не хватило денег**! Ваш баланс: {user.balance} {value_emoji}* "
#                                    f"[Это сообщение можно удалить]")
#         else:
#             user.balance -= item.price
#             await add_item(user.id, guild.id, self.item_name)
#             await interaction.send(f"*Вы приобрели **{self.item_name}**! Ваш баланс: {user.balance} {value_emoji}* "
#                                    f"[Это сообщение можно удалить]")
#
#         DB_SESSION.commit()
#
#
# class ShopView(nextcord.ui.View):
#     def __init__(self, bot, items):
#         super().__init__()
#
#         for item in items:
#             self.add_item(ShopButton(bot, item.name))


class ServerSetupCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ФУНКЦИЯ, обновляющая магазин
    @staticmethod
    async def store_update(guild: nextcord.Guild):
        store_channel = get(guild.channels, name="🛒магазин")
        if store_channel:
            # Удаление сообщений
            await store_channel.purge(limit=None)

            # Список всех предметов
            all_items = DB_SESSION.query(Items).all()
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
                        value=f"➢ **Цена:** {item.price} {EMOJIS['Валюта']}"
                              f"```fix\nОписание: {item.description} Тип: {item_type[item.type]}```", inline=False
                    )

                # Создание кнопок для сообщение
                # shop_view = ShopView(self.bot, items)

                # Отправка сообщения
                # await store_channel.send(embed=embed, view=shop_view)

    # TODO: оптимизировать логику обновления магазина
    # ФУНКЦИЯ, проверяющая нужно ли обновить магазин
    async def store_update_cycle(self):
        while True:
            if datetime.now().strftime("%H:%M") == TIME_STORE_UPDATE:
                for guild in self.bot.guilds:
                    await self.store_update(guild)
            await asyncio.sleep(60)

    # TODO: проигрывание музыки надо переделать, так как общей категории с главной темой нет
    # TODO: разобраться как делать плейлисты для воспроизведения
    # TODO: составить плейлист под сеттинг бота и поставить его на воспроизведение
    # ФУНКЦИЯ, подключение к каналу "🎶Главная тема" на всех серверах
    # async def channel_connection(self):
    #     for guild in self.bot.guilds:
    #         voice_channel = get(guild.voice_channels, name="🎶Главная тема")
    #         if voice_channel:
    #             try:
    #                 # Подключение к каналу
    #                 voice = await voice_channel.connect()
    #                 # Включение музыки
    #                 video = make_new_video(VIDEO_LINK)
    #                 audio = video.getbestaudio().url
    #                 voice.play(FFmpegPCMAudio(audio, **FFMPEG_OPTIONS, executable="ffmpeg/bin/ffmpeg.exe"))
    #             except Exception as e:
    #                 print(e)

    # # ФУНКЦИЯ, отправляющаю сообщение в чат регистрации
    # @staticmethod
    # async def send_registration_msg(channel):
    #     await channel.send(f"**В этом чате вы должны создать своего персонажа.**\n"
    #                        f"*Подходите к этому вопросу с умом!*")
    #
    #     # ======= ВЫБОР РАСЫ
    #     nation_embed = nextcord.Embed(title='⮮ __**Выбор расы:**__', color=44444)
    #     nation_embed.add_field(
    #         name='**Важно:**',
    #         value='*```yaml\n'
    #               '➢ От расы зависят некоторые характеристики.\n'
    #               '➢ Пока вы не завершите создание профиля вы можете перевыбирать расу.```*',
    #         inline=False)
    #
    #     # ======= ВЫБОР ПРОИСХОЖДЕНИЯ
    #     origin_embed = nextcord.Embed(title='⮮ __**Выбор происхождения:**__', color=44444)
    #     origin_embed.add_field(
    #         name='**Важно:**',
    #         value='*```yaml\n'
    #               '➢ От происхождения зависят некоторые характеристики.\n'
    #               '➢ Пока вы не завершите создание профиля вы можете перевыбирать происхождение.```*',
    #         inline=False
    #     )
    #
    #     # ======= СОЗДАНИЕ ИМЕНИ
    #     name_embed = nextcord.Embed(title='⮮ __**Ваше имя:**__', color=44444)
    #     name_embed.add_field(
    #         name='**Важно:**',
    #         value='*```yaml\n'
    #               '➢ Желаемое вами имя напишите в данный чат с помощью команды: "/name".\n'
    #               '➢ Имя не влияет на характеристики, при написании команды напишите имя маленькими буквами.\n'
    #               '➢ Вводите имя с умом так как его можно будет изменить только через админа.\n'
    #               '➢ После написания имени вы завершите создание профиля.```*',
    #         inline=False
    #     )
    #
    #     await channel.send(
    #         embed=nation_embed,
    #         view=NationView()
    #     )
    #     await channel.send(
    #         embed=origin_embed,
    #         view=OriginView()
    #     )
    #     await channel.send(embed=name_embed)

    # ФУНКЦИЯ, записывающая всех с сервера в базу данных
    @staticmethod
    async def write_db(guild: nextcord.Guild):
        check_write_db = False
        for member in guild.members:
            user_id = f"{member.id}-{guild.id}"
            if not member.bot and not DB_SESSION.query(User).filter(User.id == user_id).first():
                user = User()
                user.id = user_id

                DB_SESSION.add(user)
                check_write_db = True
        DB_SESSION.commit()
        return check_write_db

    # ФУНКЦИЯ, удаляющая всех с сервера из базы данных
    @staticmethod
    async def delete_db(guild: nextcord.Guild):
        for member in guild.members:
            user = DB_SESSION.query(User).filter(User.id == f"{member.id}-{guild.id}").first()
            if not member.bot and user:
                DB_SESSION.delete(user)
        DB_SESSION.commit()

    # ФУНКЦИЯ, создающая чаты
    @staticmethod
    async def create_channel(
            guild: nextcord.Guild,
            channel_info: dict,
            category: nextcord.CategoryChannel,
            title: str,
            roles_for_permss: dict
    ):
        kind, allow_messaging, pos = channel_info
        channel = None

        # Создание чата
        if not get(guild.channels, name=title):
            channel = await guild.create_text_channel(title, category=category, position=pos)
            # Настройка доступа к чату
            if kind != 'all':
                for role_name, role in roles_for_permss.items():
                    await channel.set_permissions(
                        role,
                        send_messages=allow_messaging,
                        read_messages=kind == role_name
                    )

        return channel

    @nextcord.slash_command(
        description="Gain all basic information you need about game's setting.",
        description_localizations={
            Locale.ru: "Получить общую информацию о сеттинге игры"
        },
        guild_ids=TEST_GUILDS_ID
    )
    async def game_information(self, interaction: Interaction):
        history_embed = nextcord.Embed(title='⮮ __**История:**__', color=0x7db1ff)
        history_embed.add_field(
            name='\u200b',
            value='*```yaml\n'
                  '\tОколо века назад человечество смогло покинуть Землю и освоить Марс, '
                  'на нём люди нашли руду под названием Экзорий. Люди тщательно изучали Экзорий, '
                  'и открыли для себя много разных свойств этой руды, в результате многих экспериментов '
                  'люди смогли извлекать из этой руды много энергии с огромной мощью. В ходе таких '
                  'открытий люди смогли быстро развить технологии и освоить космос намного лучше, '
                  'человечество стало путешествовать и колонизировать различные планеты в различных '
                  'звёздных системах.\n\n'
                  '\tЗемля в своё время, к сожалению стала деградировать, из за экспериментов '
                  'которые проводили на Земле и людей отвергающих новые технологии, родная планета '
                  'человечества через некоторое время стала скверным местом. На Землю стали отправлять '
                  'неугодных людей, которые совершали какие либо преступление. Уже несколько поколений люди '
                  'с планеты Земля живут в ужасном мире этой планеты. Вы родились на Земле, и вам '
                  'предстоит на ней выжить.```*',
            inline=False
        )

        # ======= Инфо
        info_embed = nextcord.Embed(title='⮮ __**Дополнительная информация:**__', color=0x7db1ff)
        info_embed.add_field(
            name='\u200b',
            value='*```yaml\n'
                  '➢ Для того что бы узнать команды, напишите в чате "/", вам предоставится '
                  'список команд с их описаниями.\n'
                  '➢ Основная валюта игры: "Gaudium".\n'
                  '➢ Если у вас возникла ошибка обращайтесь к администрации.```*',
            inline=False
        )

        await interaction.send(embed=history_embed, ephemeral=True)
        await interaction.send(embed=info_embed, ephemeral=True)

    # КОМАНДА, настраивающая сервер
    @nextcord.slash_command(
        description="Install bot to get all of the functions.",
        description_localizations={
            Locale.ru: "Команда, с помощью которой можно подключить бота к серверу."
        },
        default_member_permissions=Permissions(administrator=True),
        guild_ids=TEST_GUILDS_ID
    )
    async def setup_server(self, interaction: Interaction):
        guild = interaction.guild
        check_implement = False
        permission_roles = {}

        # Создание ролей
        for role_name, color in GAME_ROLES_COLORS.items():
            permission_roles[role_name] = get(guild.roles, name=role_name)
            if not get(guild.roles, name=role_name):
                await guild.create_role(name=role_name, color=color)
                await interaction.send(
                    f":white_check_mark: *Роль {role_name} создана.*",
                    ephemeral=True
                )
                check_implement = True

        # Создание чатов и категорий
        for category_name, channels in OBJECTS.items():
            # Создание категории
            category = get(guild.categories, name=category_name)
            if not category:
                category = await guild.create_category(category_name)
                check_implement = True

            # Создание чатов
            for channel_name in channels.keys():
                channel = await self.create_channel(
                    guild,
                    channels[channel_name].values(),
                    category,
                    channel_name,
                    permission_roles
                )
                if channel:
                    check_implement = True
                    # if channel.name == "🚪создание-персонажа":
                    #     await self.send_registration_msg(get(guild.channels, name="🚪создание-персонажа"))

            await interaction.send(
                f":white_check_mark: *Категория {category_name} создана.*",
                ephemeral=True
            )

            # Добавление чатов в категорию (сделано для повторного /implement)
            for channel_name in channels.keys():
                await get(guild.channels, name=channel_name).edit(category=category)

        # Создание канала для прослушивания музыки
        # name_voice = "🎶Главная тема"
        # if not get(guild.voice_channels, name=name_voice):
        #     channel = await guild.create_voice_channel(name_voice,
        #                                                category=get(guild.categories, name="ОБЩЕЕ"), position=4)
        #     await channel.set_permissions(permission_roles["non-game"], speak=False, view_channel=False)
        #     await channel.set_permissions(permission_roles["game"], speak=False, view_channel=True)
        #     check_implement = True

        # Заполнение базы данных
        if await self.write_db(guild):
            await interaction.send(
                ":white_check_mark: *База данных заполнена.*",
                ephemeral=True
            )
            check_implement = True

        # Создание магазина
        await self.store_update(guild)

        # Подключение к каналу "🎶Главная тема"
        # await self.channel_connection()

        # Уведомление
        if check_implement:
            await interaction.send(":white_check_mark: **Готово!**", ephemeral=True)
            return

        await interaction.send(":x: **Первоначальная настройка уже была произведена!**", ephemeral=True)

    # КОМАНДА, удаляющая настройку сервера
    @commands.command()
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
            user = DB_SESSION.query(User).filter(User.id == f"{member.id}-{guild.id}").first()
            if not member.bot and user:
                DB_SESSION.delete(user)
                chek_delete_db = True
        DB_SESSION.commit()

        # Уведомление
        if chek_delete_db:
            await interaction.send(":white_check_mark: **Готово!**")
            return

        await interaction.send(":x: **Пользователей нет в базе данных!**")

    # @bot_install.error
    # async def install_error(
    #         self,
    #         interaction: Interaction,
    #         error: Exception
    # ):
    #     await throw_error(interaction, error)


def setup(bot):
    bot.add_cog(ServerSetupCog(bot))
