from nextcord import ButtonStyle

from general_imports import *
from cogs.user_experience import get_paged_inventory, get_paged_embed_inventory, get_inventory

# TODO: оптимизировать код
# TODO: улучшить дизайн команд
# TODO: убрать ненужные ephemeral из сообщений
# TODO: добавить локализацию выводов для англ и рус языков
# TODO: избавиться от багов


class ConfirmTradeView(nextcord.ui.View):
    def __init__(
            self,
            guild_id: int,
            sender: nextcord.Member,
            recipient: nextcord.Member,
            sender_items: Optional[str],
            recipient_items: Optional[str]
    ):
        super().__init__(timeout=None)

        self.guild_id = guild_id
        self.sender = sender
        self.recipient = recipient
        self.sender_items = sender_items.split("\n") if sender_items else None
        self.recipient_items = recipient_items.split("\n") if recipient_items else None

    @nextcord.ui.button(label="Принять обмен", style=ButtonStyle.green)
    async def confirm_trade(
            self,
            button: nextcord.ui.Button,
            interaction: Interaction
    ):
        if self.sender_items:
            await swap_items(
                self.guild_id,
                self.sender_items,
                self.sender.id,
                self.recipient.id
            )
        if self.recipient_items:
            await swap_items(
                self.guild_id,
                self.recipient_items,
                self.recipient.id,
                self.sender.id
            )

        await self.sender.send(f":white_check_mark: {self.recipient.name} принял обмен!")
        await self.recipient.send(":white_check_mark: Обмен принят!")

        await interaction.message.delete()

    @nextcord.ui.button(label="Отклонить обмен", style=ButtonStyle.red)
    async def decline_trade(
            self,
            button: nextcord.ui.Button,
            interaction: Interaction
    ):
        await self.sender.send(f":x: {self.recipient.name} не принял обмен!")
        await self.recipient.send(":white_check_mark: Обмен успешно отменён!")

        await interaction.message.delete()


class ItemSelectionView(Paginator):
    def __init__(
            self,
            pages: list,
            paged_inventory: list,
            player: nextcord.Member
    ):
        super().__init__(
            pages,
            extra_item=ItemsDropdown(self, paged_inventory) if paged_inventory else None
        )

        self.player = player
        self.trade_items = [[]]
        self.message = None


class ItemsDropdown(nextcord.ui.Select):
    def __init__(
            self,
            parent: ItemSelectionView,
            paged_inventory: list
    ):
        self.paged_inventory = paged_inventory
        self.parent = parent

        options = []
        self.parent.trade_items = [[] * len(self.paged_inventory)]

        for item, amount in self.paged_inventory[0].items():
            item_name = DB_SESSION.query(Items).filter(Items.id == item).first().name
            options.append(nextcord.SelectOption(
                label=item_name, description=f"Количество: {amount}"
            ))

        super().__init__(
            placeholder="Выберите нужные предметы",
            min_values=0,
            max_values=len(options),
            options=options,
        )

    async def callback(self, interaction: Interaction):
        self.parent.trade_items[self.parent.current_page] = self.values

    async def update(self):
        options = []
        for item, amount in self.paged_inventory[self.parent.current_page].items():
            options.append(nextcord.SelectOption(
                label=item, description=f"Количество: {amount}"
            ))

        self.max_values = len(options)
        self.options = options


class SendTradeView(nextcord.ui.View):
    def __init__(
            self,
            sender_view: Optional[ItemSelectionView],
            recipient_view: Optional[ItemSelectionView]
    ):
        super().__init__(timeout=None)

        self.sender_view = sender_view
        self.recipient_view = recipient_view
        self.sent = False

    @nextcord.ui.button(label="Отправить обмен", style=ButtonStyle.green)
    async def send_trade(
            self,
            button: nextcord.ui.Button,
            interaction: Interaction
    ):
        if self.sent:
            await interaction.send(
                ":x: Этот обмен уже был отправлен. Для повтороной отправки создайте новое предложение.",
                ephemeral=True
            )
            return

        sender_items = await self.normalize_trade_items(self.sender_view.trade_items)
        recipient_items = await self.normalize_trade_items(self.recipient_view.trade_items)

        if not (sender_items or recipient_items):
            await interaction.send(":x: Обмен не отправлен. Ни одного предмета не выбрано.", ephemeral=True)
            return

        embed = nextcord.Embed(
            title="**Вам отправлен обмен**",
            color=0xFFFFF0
        )

        embed.add_field(
            name=f"{self.sender_view.player.name}\nПредметы :",
            value=sender_items if sender_items else "Пусто"
        )
        embed.add_field(name="\u200b", value="\u200b")
        embed.add_field(
            name=f"{self.recipient_view.player.name}\nПредметы:",
            value=recipient_items if recipient_items else "Пусто"
        )

        await self.recipient_view.player.send(
            embed=embed,
            view=ConfirmTradeView(
                interaction.guild_id,
                self.sender_view.player,
                self.recipient_view.player,
                sender_items,
                recipient_items
            )
        )

        await interaction.send("Обмен отправлен!", ephemeral=True)

        await self.sender_view.message.edit(view=nextcord.ui.View())
        await self.recipient_view.message.edit(view=nextcord.ui.View())
        self.sent = True

    @staticmethod
    async def normalize_trade_items(trade_items: list) -> Optional[str]:
        if trade_items:
            return "\n".join(["\n".join(item_row) for item_row in trade_items])
        return None


class TradeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(
        name="trade",
        description="Command to create send offer to other player",
        description_localizations={
            Locale.ru: "Команда, с помощью которой можно сформировать предложение обмена другому игроку."
        },
        guild_ids=TEST_GUILDS_ID
    )
    @application_checks.has_role("Игрок")
    async def trade(
            self,
            interaction: Interaction,
            member: nextcord.Member = SlashOption(
                name="recipient",
                name_localizations={
                    Locale.ru: "получатель"
                },
                description="User who will recieve this trade offer",
                description_localizations={
                    Locale.ru: "Пользователь, которому будет отправлен обмен"
                },
                required=True
            )
    ):
        user = interaction.user
        guild = interaction.guild

        trade_errors = LOCALIZATIONS["Errors"]["Trade"]
        user_locale = interaction.locale[:2]

        if user == member:
            raise IncorrectUser(trade_errors["Self-trade"][user_locale])

        if member.bot:
            raise IncorrectUser(trade_errors["Self-trade"][user_locale])

        if get(guild.roles, name="Игрок") not in member.roles:
            raise IncorrectUser(trade_errors["Missing-role"][user_locale].format(member.name))

        if not (await get_inventory(user.id, guild.id) or await get_inventory(member.id, guild.id)):
            raise MissingItems(trade_errors["Missing-items"][user_locale].format(member.name))

        sender_view = await self.send_trade_view(interaction, user, guild.id)
        recipient_view = await self.send_trade_view(interaction, member, guild.id)

        await interaction.send(
            view=SendTradeView(sender_view, recipient_view),
            ephemeral=True
        )

    @staticmethod
    async def send_trade_view(
            interaction: Interaction,
            user: nextcord.Member,
            guild_id: int
    ) -> ItemSelectionView:
        embeds = await get_paged_embed_inventory(user, guild_id, 10)
        paged_inventory = await get_paged_inventory(user.id, guild_id, 10)
        view = ItemSelectionView(embeds, paged_inventory, user)

        message = await interaction.send(
            embed=embeds[0],
            view=view,
            ephemeral=True
        )
        if not message:
            message = await interaction.original_message()

        view.message = message

        return view

    # КОМАНДА, перевод денег
    @nextcord.slash_command(
        name="transfer_money",
        description="Command to transfer money to other player",
        description_localizations={
            Locale.ru: "Команда, с помощью которой можно перевести деньги другому игроку."
        },
        guild_ids=TEST_GUILDS_ID
    )
    async def transfer_money(
            self,
            interaction: Interaction,
            member: nextcord.Member = SlashOption(
                name="recipient",
                name_localizations={
                    Locale.ru: "получатель"
                },
                description="User who will recieve money",
                description_localizations={
                    Locale.ru: "Пользователь, которому будут переведены деньги"
                },
                required=True
            ),
            amount: int = SlashOption(
                name="amount",
                name_localizations={
                    Locale.ru: "сумма"
                },
                description="Amount of money to send",
                description_localizations={
                    Locale.ru: "Сумма для отправки"
                },
                required=True
            )
    ):
        guild = interaction.guild
        player_role = get(guild.roles, name="Игрок")
        player = interaction.user

        if player_role not in player.roles:
            raise IncorrectUser("- У Вас нет роли \"Игрок\"!")
        if member.bot:
            raise IncorrectUser("- Ботам передавать деньги нельзя!\n"
                                "(Я бы в принципе не доверял им, кроме меня, конечно, я лучший бот, почти человек!)")
        if player_role not in member.roles:
            raise IncorrectUser(f"- У {member.name} нет роли \"Игрок\"!")

        player_user = DB_SESSION.query(User).filter(User.id == f"{player.id}-{guild.id}").first()
        member_user = DB_SESSION.query(User).filter(User.id == f"{member.id}-{guild.id}").first()

        if amount < 1:
            raise IncorrectMemberAmount(f"- Минимальная сумма перевода равна 1 Gaudium!")
        if player_user.balance < amount:
            raise IncorrectMemberAmount(f"- У {player_user.name} нет столько денег!")

        value_emoji = EMOJIS["Валюта"]
        player_user.balance -= amount
        member_user.balance += amount

        await interaction.send(f":white_check_mark: {member.name} получил "
                               f"{amount} {value_emoji}")
        await member.send(f"Только что {player.name} перевёл Вам {amount} {value_emoji}")
        DB_SESSION.commit()

    @trade.error
    async def trade_error(
            self,
            interaction: Interaction,
            error: Exception
    ):
        await throw_error(interaction, error)

    @transfer_money.error
    async def money_transfer_error(
            self,
            interaction: Interaction,
            error: Exception
    ):
        await throw_error(interaction, error)


# ФУНКЦИЯ, добавляющая предмет в инвентарь
async def add_item(
        player_id: int,
        guild_id: int,
        item: int
):
    user = DB_SESSION.query(User).filter(User.id == f"{player_id}-{guild_id}").first()
    user.inventory += f"{';' if user.inventory != '' else ''}{item}"
    DB_SESSION.commit()


# ФУНКЦИЯ, которая убирает предмет из инвентаря
async def remove_item(
        player_id: int,
        guild_id: int,
        item_id: int
):
    user = DB_SESSION.query(User).filter(User.id == f"{player_id}-{guild_id}").first()
    inventory_list = user.inventory.split(";")
    inventory_list.remove(str(item_id))
    user.inventory = ";".join(inventory_list)
    DB_SESSION.commit()


# ФУНКЦИЯ, которая передаёт предметы из одного инвентаря в другой
async def swap_items(
        guild_id: int,
        item_names: list,
        sender_id: int,
        recipient_id: int
):
    for item_name in item_names:
        item_id = DB_SESSION.query(Items).filter(Items.name == item_name).first().id

        await remove_item(sender_id, guild_id, item_id)
        await add_item(recipient_id, guild_id, item_id)


def setup(bot):
    bot.add_cog(TradeCog(bot))
