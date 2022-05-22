import asyncio
from typing import Optional

from nextcord.ext import commands
from nextcord import Interaction, SlashOption
from nextcord.utils import get

from constants import *


class InventoryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # КОМАНДА, перемещение между городами
    @nextcord.slash_command(
        name="отправиться",
        description="Команда, с помощью которой можно отправиться в другой город.",
        guild_ids=TEST_GUILDS_ID
    )
    async def move(
            self,
            interaction: Interaction,
            city_name: str = SlashOption(
                name="пункт_назначения",
                description="Название города, в который Вы хотите отправится.",
                choices={
                    "Тополис": "Тополис",
                    "Браифаст": "Браифаст",
                    "Джадифф": "Джадифф"
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

        speed = db_sess.query(User).filter(User.id == f"{user.id}-{guild.id}").first().speed

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
        await get(guild.channels, name=f"таверна-{city_name[0].lower()}").send(f"{user.mention} *прибыл!*")
        await user.send(f":white_check_mark: **С прибытием в {city_name}.**")

    # КОМАНДА, для вливания скилл поинтов в характеристики
    @nextcord.slash_command(
        name="открыть_профиль",
        description="Команда, с помощь которой можно посмотреть игровой профиль.",
        guild_ids=TEST_GUILDS_ID
    )
    async def profile(
            self,
            interaction: Interaction,
            member: Optional[nextcord.Member] = SlashOption(
                name="игрок",
                description="Пользователь, профиль которого Вы хотите открыть"
            )
    ):
        guild = interaction.guild
        user = interaction.user if not member else member

        if get(guild.roles, name="Игрок") not in interaction.user.roles:
            raise IncorrectUser("- У Вас нет роли \"Игрок\"!")
        if user:
            if user.bot:
                raise IncorrectUser("- У ботов нет инвентаря!\n"
                                    "Даже не пытайтесь открыть у них инвентарь - это бесполезно!")
            if get(guild.roles, name="Игрок") not in member.roles:
                raise IncorrectUser(f"- У {member.name} нет роли \"Игрок\"!")

        db_user = db_sess.query(User).filter(User.id == f"{user.id}-{guild.id}").first()

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

        # if user.skill_points > 0:
        #     buttons = [Button(style=ButtonStyle.blue, label=f"Улучшить {elem}") for elem in \
        #                ['здоровье', 'силу', 'интелект', 'маторику', 'скорость']]
        #     await ctx.channel.send(
        #         embed=embed,
        #         components=[buttons]
        #     )
        # else:
        await interaction.send(embed=embed, ephemeral=True)

    # КОМАНДА, открывающая инвентарь
    @nextcord.slash_command(
        name="открыть_инвентарь",
        description="Команда, с помощью которой можно открыть и свой, и чужой инвентарь.",
        guild_ids=TEST_GUILDS_ID
    )
    async def open_inventory(
            self,
            interaction: Interaction,
            member: Optional[nextcord.Member] = SlashOption(
                name="игрок",
                description="Пользователь, инвентарь которого Вы хотите открыть",
                required=False
            )
    ):
        guild = interaction.guild
        player = member if member else interaction.user

        if get(guild.roles, name="Игрок") not in interaction.user.roles:
            raise IncorrectUser("- У Вас нет роли \"Игрок\"!")
        if player:
            if player.bot:
                raise IncorrectUser("- У ботов нет инвентаря!\n"
                                    "Даже не пытайтесь открыть у них инвентарь - это бесполезно!")
            if get(guild.roles, name="Игрок") not in member.roles:
                raise IncorrectUser(f"- У {member.name} нет роли \"Игрок\"!")

        value_emoji = self.bot.get_emoji(EMOJIS_ID["Валюта"])
        player_inventory = get_inventory(player.id, guild.id)
        player_db = db_sess.query(User).filter(User.id == f"{player.id}-{guild.id}").first()
        embed = nextcord.Embed(title=f"**˹ Инвентарь __{player_db.name.upper()}__˼**",
                               description=f"**Баланс: {player_db.balance} Gaudium**", color=0xFFFFF0)

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
            embed.add_field(name="\u200b", value="**Здесь пусто, вообще ничего!**")

        embed.set_thumbnail(url=player.avatar.url)
        embed.set_footer(text=f"Никнейм в Discord: {player.name}")

        await interaction.send(embed=embed, ephemeral=True)

    @move.error
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

    @open_inventory.error
    async def open_inventory_error(
            self,
            interaction: Interaction,
            error: Exception
    ):
        await throw_error(interaction, error)


def get_page_embed_inventory(inventory, current_page, title):
    embed = nextcord.Embed(
        title=f"**˹ {title} ˼**",
        description=f"Страница: {current_page}",
        color=0xFFFFF0
    )

    counter = 1
    for item in inventory.keys():
        price = db_sess.query(Items).filter(Items.name == item).first().price
        embed.add_field(name=f"{counter}. {item}", value=f"Цена: {price} Gaudium")
        counter += 1

    return embed


def get_paged_inventory(player_id, guild_id, max_amount_on_page):
    stripped_user_inventory = [{}]
    user_inventory = get_inventory(player_id, guild_id)
    index, page = 0, 0

    for item, amount in user_inventory.items():
        stripped_user_inventory[page][item] = amount
        index += 1
        if index >= max_amount_on_page:
            index = 0
            page += 1
            stripped_user_inventory.append({})

    if index == 0 and page == 0:
        return None
    return stripped_user_inventory


# ФУНКЦИЯ, которая получает инвентарь игрока формата - {предмет:количество}
def get_inventory(player_id: int, guild_id: int):
    user_inventory = db_sess.query(User).filter(User.id == f"{player_id}-{guild_id}").first().inventory
    player_inventory = {}
    if len(user_inventory) != 0:
        for item in user_inventory.split(";"):
            player_inventory[item] = player_inventory.get(item, 0) + 1
    return player_inventory


# ФУНКЦИЯ, добавляющая xp, lvl
def add_xp(guild_id: int, member_id: int, xp: int):
    user = db_sess.query(User).filter(User.id == f"{member_id}-{guild_id}").first()
    user.xp += xp
    need_xp = 500 * user.level * (user.level - 0.5)
    if user.xp >= need_xp:
        user.xp = user.xp % need_xp
        user.level += 1
        user.skill_points += 1
    db_sess.commit()


def setup(bot):
    bot.add_cog(InventoryCog(bot))
