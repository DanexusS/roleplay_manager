from nextcord.ext import commands
from nextcord import Interaction, SlashOption
from nextcord.utils import get
from nextcord import ButtonStyle

from constants import *
from cogs.user_experience import get_paged_inventory, get_page_embed_inventory


class TradeMember:
    def __init__(self, player, items):
        self.player = player
        self.items = items


class ConfirmTradeView(nextcord.ui.View):
    def __init__(self, guild_id, sender, recipient):
        super().__init__(timeout=None)

        self.guild_id = guild_id
        self.sender = sender
        self.recipient = recipient

    @nextcord.ui.button(label="Принять обмен", style=ButtonStyle.green)
    async def confirm_trade(self, button: nextcord.ui.Button, interaction: Interaction):
        if self.sender.items or "Ничего" not in self.sender.items:
            swap_items(self.guild_id, self.sender.items, self.sender.player.id, self.recipient.player.id)
        if self.recipient.items or "Ничего" not in self.recipient.items:
            swap_items(self.guild_id, self.recipient.items, self.recipient.player.id, self.sender.player.id)

        await self.sender.player.send(f":white_check_mark: {self.recipient.player.name} принял обмен!")
        await self.recipient.player.send("Обмен принят!")

        await interaction.message.delete()

    @nextcord.ui.button(label="Отклонить обмен", style=ButtonStyle.red)
    async def decline_trade(self, button: nextcord.ui.Button, interaction: Interaction):
        await self.sender.player.send(f":x: {self.recipient.player.name} не принял обмен!")
        await self.recipient.player.send(":white_check_mark: Обмен успешно отменён!")

        await interaction.message.delete()


class SendTradeView(nextcord.ui.View):
    def __init__(self, sender_view, recipient_view):
        super().__init__(timeout=None)

        self.sender_view = sender_view
        self.recipient_view = recipient_view

    @nextcord.ui.button(label="Отправить обмен", style=ButtonStyle.green)
    async def send_trade(self, button: nextcord.ui.Button, interaction: Interaction):
        sender_items = "\n".join(["\n".join(item_row) for item_row in self.sender_view.trade_items])
        recipient_items = "\n".join(["\n".join(item_row) for item_row in self.recipient_view.trade_items])

        if not sender_items and not recipient_items or \
                sender_items == "Ничего" and recipient_items == "Ничего":
            return

        embed = nextcord.Embed(
            title="**˹ Вам отправлен обмен ˼**",
            description="\u200b",
            color=0xFFFFF0
        )

        embed.add_field(
            name=f"{self.sender_view.player.name}\nПредметы :",
            value=sender_items if sender_items or sender_items == "Ничего" else "Пусто"
        )
        embed.add_field(name="\u200b", value="\u200b")
        embed.add_field(
            name=f"{self.recipient_view.player.name}\nПредметы:",
            value=recipient_items if recipient_items or recipient_items == "Ничего" else "Пусто"
        )

        await self.recipient_view.player.send(
            embed=embed,
            view=ConfirmTradeView(
                self.sender_view.guild_id,
                TradeMember(self.sender_view.player, sender_items.split("\n")),
                TradeMember(self.recipient_view.player, recipient_items.split("\n"))
            )
        )
        await interaction.send("Обмен отправлен!")

        channel = await self.sender_view.player.create_dm()
        for message in await channel.history(limit=1000).flatten():
            try:
                child = message.components[0].children[0]
                if isinstance(child, nextcord.SelectMenu) or isinstance(child, nextcord.Button):
                    await message.delete()
            except IndexError:
                continue


class ItemsDropdown(nextcord.ui.Select):
    def __init__(self, parent, guild_id, player, text):
        self.stripped_player_inventory = get_paged_inventory(player.id, guild_id, 25)
        self.parent = parent

        if self.stripped_player_inventory:
            self.parent.trade_items = [[] * len(self.stripped_player_inventory)]

            options = []

            for item, amount in self.stripped_player_inventory[self.parent.current_page].items():
                options.append(nextcord.SelectOption(
                    label=item, description=f"Количество: {amount}"
                ))
        else:
            options = [nextcord.SelectOption(label="Ничего")]

        super().__init__(
            placeholder=text,
            min_values=0,
            max_values=len(options),
            options=options,
        )

    async def callback(self, interaction: Interaction):
        self.parent.trade_items[self.parent.current_page] = self.values

    async def update(self):
        options = []
        try:
            for item, amount in self.stripped_player_inventory[self.parent.current_page].items():
                options.append(nextcord.SelectOption(
                    label=item, description=f"Количество: {amount}"
                ))
        except IndexError:
            return

        self.max_values = len(options)
        self.options = options


class PageButton(nextcord.ui.Button):
    def __init__(self, parent, emoji, direction):
        super().__init__(emoji=emoji)

        self.parent = parent
        self.direction = direction

    async def callback(self, interaction: Interaction):
        if 0 <= self.parent.current_page + self.direction <= len(self.parent.trade_items):
            self.parent.current_page += self.direction
            for child in self.parent.children:
                if not isinstance(child, PageButton):
                    await child.update()

            await self.parent.update_message(interaction.message)


class PageNumberButton(nextcord.ui.Button):
    def __init__(self, parent):
        super().__init__(label=f"Страница {parent.current_page + 1}")

        self.parent = parent
        self.disabled = True

    async def update(self):
        self.label = f"Страница {self.parent.current_page + 1}"


class ItemSelectionView(nextcord.ui.View):
    def __init__(self, guild_id, player, text, title):
        super().__init__()

        self.current_page = 0
        self.trade_items = [[]]
        self.player = player
        self.guild_id = guild_id

        self.embed_title = title

        self.add_item(ItemsDropdown(self, guild_id, player, text))
        self.add_item(PageButton(self, "⬅️", -1))
        self.add_item(PageNumberButton(self))
        self.add_item(PageButton(self, "➡️", 1))

    async def update_message(self, message):
        await message.edit(
            view=None
        )
        await message.edit(
            embed=get_page_embed_inventory(
                self.children[0].stripped_player_inventory[self.current_page],
                self.current_page + 1,
                self.embed_title
            ),
            view=self
        )


class TradeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(
        name="trade",
        description="Отправить предложение обмена другому игроку.",
        guild_ids=TEST_GUILDS_ID
    )
    async def trade(
            self,
            interaction: Interaction,
            member: nextcord.Member
    ):
        user = interaction.user
        guild_id = interaction.guild_id
        guild = interaction.guild

        if user == member:
            raise IncorrectUser("- Совершать обмены с самим собой невозможно!\n"
                                "Если вам не с кем обмениваться, то стоит поискать друзей?")
        if member.bot:
            raise IncorrectUser("- Нельзя обмениваться с Ботами!")
        if get(guild.roles, name="Игрок") not in member.roles:
            raise IncorrectUser(f"- У {member.name} нет роли \"Игрок\"!")

        user_inventory = get_paged_inventory(interaction.user.id, interaction.guild_id, 25)
        member_inventory = get_paged_inventory(member.id, interaction.guild_id, 25)

        user_view = ItemSelectionView(
            guild_id,
            user,
            "Выберете предметы из вашего инвентаря:",
            "Ваш инвентарь"
        )
        member_view = ItemSelectionView(
            guild_id,
            member,
            f"Выберете предметы из инвентаря {member.name}:",
            f"Инвентарь {member.name}"
        )

        await user.send(
            embed=get_page_embed_inventory(user_inventory[0], 1, "Ваш инвентарь") if user_inventory else None,
            view=user_view
        )
        await user.send(
            embed=get_page_embed_inventory(member_inventory[0], 1, f"Инвентарь {member.name}") if member_inventory else None,
            view=member_view
        )
        await user.send(
            view=SendTradeView(user_view, member_view)
        )

    # КОМАНДА, перевод денег
    @nextcord.slash_command(
        name="money_transfer",
        description="Отправить деньги другому игроку.",
        guild_ids=TEST_GUILDS_ID
    )
    @commands.has_role("Игрок")
    async def money_transfer(
            self,
            interaction: Interaction,
            member: nextcord.Member = SlashOption(
                description="Пользователь, которому будут переведены деньги",
                required=True
            ),
            amount: int = SlashOption(
                description="Количество денег для отправки",
                required=True
            )
    ):
        guild = interaction.guild
        if member.bot:
            raise IncorrectUser("- Ботам передавать деньги нельзя!\n"
                                "(Я бы в принципе не доверял им, кроме меня, конечно, я лучший бот, почти человек!)")
        if get(guild.roles, name="Игрок") not in member.roles:
            raise IncorrectUser(f"- У {member.name} нет роли \"Игрок\"!")

        player = interaction.user
        player_user = db_sess.query(User).filter(User.id == f"{player.id}-{guild.id}").first()
        member_user = db_sess.query(User).filter(User.id == f"{member.id}-{guild.id}").first()

        if amount < 1:
            raise IncorrectMemberAmount(f"- Минимальная сумма перевода = 1!")
        if player_user.balance < amount:
            raise IncorrectMemberAmount(f"- У {player_user.name} нет столько денег!")

        value_emoji = self.bot.get_emoji(EMOJIS_ID['Валюта'])
        player_user.balance -= amount
        member_user.balance += amount

        await interaction.send(f":white_check_mark: {member.name} получил "
                               f"{amount} {value_emoji}")
        await member.send(f"Только что {player.name} перевёл Вам {amount} {value_emoji}")
        db_sess.commit()


# ФУНКЦИЯ, добавляющая предмет в инвентарь
def add_item(guild_id, player_id, item):
    user = db_sess.query(User).filter(User.id == f"{player_id}-{guild_id}").first()
    user.inventory += f"{';' if user.inventory != '' else ''}{item}"
    db_sess.commit()


# ФУНКЦИЯ, которая убирает предмет из инвентаря
def remove_item(guild_id, player_id, item):
    print(item)
    user = db_sess.query(User).filter(User.id == f"{player_id}-{guild_id}").first()
    inventory_list = user.inventory.split(";")
    inventory_list.remove(item)
    user.inventory = ";".join(inventory_list)
    db_sess.commit()


# ФУНКЦИЯ, которая передаёт предметы из одного инвентаря в другой
def swap_items(guild_id, items, sender_id, other_id):
    for item in items:
        remove_item(guild_id, sender_id, item)
        add_item(guild_id, other_id, item)


def setup(bot):
    bot.add_cog(TradeCog(bot))
