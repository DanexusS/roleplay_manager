import asyncio
from general_imports import *

# TODO: оптимизировать код
# TODO: избавиться от багов
# TODO: улучшить дизайн команд
# TODO: убрать ненужные ephemeral из сообщений
# TODO: добавить локализацию выводов для англ и рус языков

# TODO: Добавить команду для прокачки характеристик
# TODO: добавить систему ивентов с дополнительными возможностями и бонусами
# TODO: добавить команду анализирования предметов


class UserExperienceCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # TODO: доработать перемещение и разобраться с неполадками
    # КОМАНДА, перемещение между городами
    @nextcord.slash_command(
        description="Command to travel to the different city.",
        description_localizations={
            Locale.ru: "Команда, с помощью которой можно отправиться в другой город."
        },
        guild_ids=TEST_GUILDS_ID
    )
    async def travel(
            self,
            interaction: Interaction,
            city_name: str = SlashOption(
                name="destination",
                name_localizations={
                    Locale.ru: "пункт_назначения"
                },
                description="Name of the city.",
                description_localizations={
                    Locale.ru: "Название города."
                },
                choices=["Topolis", "Braifast", "Jadiff"],
                choice_localizations={
                    "Topolis": {
                        Locale.ru: "Тополис"
                    },
                    "Braifast": {
                        Locale.ru: "Браифаст"
                    },
                    "Jadiff": {
                        Locale.ru: "Джадифф"
                    }
                }
            )
    ):
        guild = interaction.guild
        user = interaction.user

        if get(guild.roles, name="Игрок") not in interaction.user.roles:
            raise IncorrectUser("- У Вас нет роли \"Игрок\"!")
        if city_name in user.roles:
            await interaction.send(f":x: Вы и так находитесь в {city_name}!")
            return

        speed = DB_SESSION.query(User).filter(User.id == f"{user.id}-{guild.id}").first().speed

        # Удаление роли прошлого города
        await user.remove_roles(get(guild.roles, name="Тополис"))
        await user.remove_roles(get(guild.roles, name="Браифаст"))
        await user.remove_roles(get(guild.roles, name="Джадифф"))

        time_second = 8 * (60 - speed)

        # Уведомление
        await interaction.send(f"**{user.mention} отправился в город {city_name}.**")
        await user.send(f"**Время, в дороге: {time_second // 60} минут {time_second % 60} секунд.**")

        # Таймер
        await asyncio.sleep(time_second)
        # Добавление роли нового города
        await user.add_roles(get(guild.roles, name=city_name))

        # Уведомление
        # await get(guild.channels, name=f"таверна-{city_name[0].lower()}").send(f"{user.mention} *прибыл!*")
        await user.send(f":white_check_mark: **С прибытием в {city_name}.**")

    # TODO: Доработать и улучшить профиль игрока
    # КОМАНДА, для вливания скилл поинтов в характеристики
    @nextcord.slash_command(
        description="Command to open gaming profile.",
        description_localizations={
            Locale.ru: "Команда, с помощь которой можно посмотреть игровой профиль."
        },
        guild_ids=TEST_GUILDS_ID
    )
    async def profile(
            self,
            interaction: Interaction,
            member: Optional[nextcord.Member] = SlashOption(
                name="player",
                name_localizations={
                    Locale.ru: "игрок"
                },
                description="User whose profile you want to open",
                description_localizations={
                    Locale.ru: "Пользователь, профиль которого Вы хотите открыть"
                }
            )
    ):
        guild = interaction.guild
        user = member or interaction.user

        guild_locale = interaction.guild_locale[:2]
        user_locale = interaction.locale[:2]
        profile_errors = LOCALIZATIONS["Errors"]["Profile"]

        player_role = get(guild.roles, name=LOCALIZATIONS["General"]["Role-name"][guild_locale])

        if player_role not in interaction.user.roles:
            raise IncorrectUser(profile_errors["Missing-role"][user_locale])

        if member:
            if member.bot:
                raise IncorrectUser(profile_errors["Bot-profile"][user_locale])

            if player_role not in member.roles:
                raise IncorrectUser(profile_errors["Member-missing-role"][user_locale].format(member.name))

        db_user = DB_SESSION.query(User).filter(User.id == f"{user.id}-{guild.id}").first()

        # ======= ПРОФИЛЬ
        embed = nextcord.Embed(title=f"⮮ __**{db_user.name}:**__", color=4017407)

        embed.add_field(name='**Баланс:**', value=f"*```md\n# {db_user.balance} Gaudium```*", inline=False)
        text1 = f"*```md\n" \
                f"# Уровень ➢ {db_user.level}\n" \
                f"# Раса ➢ {db_user.nation}\n" \
                f"# Происхождение ➢ {db_user.origin}```*"
        embed.add_field(name='**Сведения:**', value=text1, inline=False)
        text2 = f"*```md\n" \
                f"# Здоровье ➢ {db_user.health}\n" \
                f"# Сила ➢ {db_user.strength}\n" \
                f"# Интелект ➢ {db_user.intelligence}\n" \
                f"# Маторика ➢ {db_user.dexterity}\n" \
                f"# Скорость ➢ {db_user.speed}```*"
        embed.add_field(name='**Характеристики:**', value=text2, inline=False)
        embed.add_field(name='**Свободных очков навыка:**', value=f"*```md\n# {db_user.skill_points}```*", inline=False)

        embed.set_thumbnail(url=user.avatar.url)
        embed.set_footer(text=f"Никнейм Discord: {user.name}")

        await interaction.send(embed=embed)

    @nextcord.slash_command(
        guild_ids=TEST_GUILDS_ID
    )
    async def skill_tree(self, interaction: Interaction):
        pass

    # КОМАНДА, открывающая инвентарь
    @nextcord.slash_command(
        description="Command to open inventory.",
        description_localizations={
            Locale.ru: "Команда, с помощью которой можно открыть инвентарь."
        },
        guild_ids=TEST_GUILDS_ID
    )
    async def inventory(
            self,
            interaction: Interaction,
            member: Optional[nextcord.Member] = SlashOption(
                name="player",
                name_localizations={
                    Locale.ru: "игрок"
                },
                description="User whose inventory you want to open.",
                description_localizations={
                    Locale.ru: "Пользователь, инвентарь которого Вы хотите открыть."
                },
                required=False
            )
    ):
        guild = interaction.guild
        player = interaction.user or member

        if get(guild.roles, name="Игрок") not in interaction.user.roles:
            raise IncorrectUser("- У Вас нет роли \"Игрок\"!")

        if member:
            if member.bot:
                raise IncorrectUser("- У ботов нет инвентаря!\n"
                                    "Даже не пытайтесь открыть у них инвентарь - это бесполезно!")

            if get(guild.roles, name="Игрок") not in member.roles:
                raise IncorrectUser(f"- У {member.name} нет роли \"Игрок\"!")

        embeds = await get_paged_embed_inventory(player, guild.id)

        await interaction.send(
            embed=embeds[0],
            view=nextcord.ui.View() if "Пусто" in embeds[0].fields[0].name else Paginator(embeds),
            ephemeral=True
        )

    @travel.error
    async def move_error(
            self,
            interaction: Interaction,
            error: Exception
    ):
        await throw_error(interaction, error)

    @profile.error
    async def profile_error(
            self,
            interaction: Interaction,
            error: Exception
    ):
        await throw_error(interaction, error)

    @inventory.error
    async def open_inventory_error(
            self,
            interaction: Interaction,
            error: Exception
    ):
        await throw_error(interaction, error)


async def get_paged_embed_inventory(
        player: nextcord.Member,
        guild_id: int,
        max_amount_on_page: int = 15
) -> list:
    player_inventory = await get_paged_inventory(player.id, guild_id, max_amount_on_page)
    player_db = DB_SESSION.query(User).filter(User.id == f"{player.id}-{guild_id}").first()

    embeds = []
    embed_base = nextcord.Embed(
        title=nextcord.Embed.Empty,
        description=nextcord.Embed.Empty,
        color=0x7db1ff
    )
    embed_base.set_author(name=f"Инвентарь игрока {player_db.name}", icon_url=player.avatar.url)
    embed_base.set_footer(text=f"Никнейм в Discord: {player.name}")

    if not player_inventory:
        embed_base.add_field(name="**Пусто**", value="\*звуки сверчков\*")
        return [embed_base]

    for page in player_inventory:
        embed = embed_base
        items = []

        for item_id, amount in page.items():
            item_obj = DB_SESSION.query(Items).filter(Items.id == item_id).first()
            items.append(f"**{item_obj.name}**: {amount}")

        embed.add_field(name="**Предметы:**", value="\n".join(items))
        embeds.append(embed)

    return embeds


async def get_paged_inventory(
        player_id: int,
        guild_id: int,
        max_amount_on_page: int
) -> Optional[list]:
    stripped_user_inventory = [{}]
    user_inventory = await get_inventory(player_id, guild_id)
    index, page = 0, 0

    if not user_inventory:
        return None

    for item, amount in user_inventory.items():
        stripped_user_inventory[page][item] = amount
        index += 1
        if index >= max_amount_on_page and len(user_inventory.keys()) != max_amount_on_page:
            index = 0
            page += 1
            stripped_user_inventory.append({})

    if index == 0 and page == 0:
        return None
    return stripped_user_inventory


# ФУНКЦИЯ, которая получает инвентарь игрока формата - {предмет:количество}
async def get_inventory(
        player_id: int,
        guild_id: int
) -> Optional[dict]:
    user_inventory = DB_SESSION.query(User).filter(User.id == f"{player_id}-{guild_id}").first().inventory
    player_inventory = {}
    if len(user_inventory) != 0:
        for item in user_inventory.split(";"):
            player_inventory[item] = player_inventory.get(item, 0) + 1

    if player_inventory == {}:
        return None
    return player_inventory


# TODO: добавить более значимую роль уровня и его прокачки
# ФУНКЦИЯ, добавляющая xp, lvl
async def add_xp(
        guild_id: int,
        member_id: int,
        xp: float
):
    user = DB_SESSION.query(User).filter(User.id == f"{member_id}-{guild_id}").first()
    user.xp += xp
    need_xp = 500 * user.level * (user.level - 0.5)
    if user.xp >= need_xp:
        user.xp = user.xp % need_xp
        user.level += 1
        user.skill_points += 1
    DB_SESSION.commit()


def setup(bot: commands.Bot):
    bot.add_cog(UserExperienceCog(bot))
