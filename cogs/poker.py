import asyncio

import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption
from nextcord.utils import get

from constants import *

from itertools import combinations

from enum import Enum
from random import shuffle, choice


RANK_INFO = {
    "6": {"value": 4},
    "7": {"value": 5},
    "8": {"value": 6},
    "9": {"value": 7},
    "10": {"value": 8},
    "Jack": {"value": 9},
    "Queen": {"value": 10},
    "King": {"value": 11},
    "Ace": {"value": 12}
}

playing_cards_emoji = {
    "Clubs": 970002047334232074,
    "Spades": 970002992470319205,
    "Diamonds": 970003739081605231,
    "Hearts": 970003997257773076
}

# cards = json.load(open("cards.json", encoding="utf8"))


class DeckOfCards:
    def __init__(self, size=36):
        self.cards = []
        # for suit, values in cards.items():
        #     for value in values[:size // 4]:
        #         self.cards.append(f"{value} - {suit}")
        # self.size = size

    async def shuffle(self):
        shuffle(self.cards)

    async def reset(self):
        self.__init__(self.size)

    async def take(self, amount):
        taken_cards = []
        for number in range(amount):
            taken_card = choice(self.cards)

            taken_cards.append(taken_card)
            self.cards.remove(taken_card)
            shuffle(self.cards)

        return taken_cards


class HandRanking(Enum):
    HIGH_CARD = 1
    PAIR = 2
    TWO_PAIR = 3
    THREE_OF_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_KIND = 8
    STRAIGHT_FLUSH = 9

    def __lt__(self, other):
        return self.value < other.value


class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

    def __lt__(self, other):
        return RANK_INFO[self.rank]["value"] < RANK_INFO[other.rank]["value"]

    def __eq__(self, other):
        return self.rank == other.rank


class Hand:
    def __init__(self, _cards):
        self.cards = sorted(_cards)
        duplicates = self.get_duplicates()

        if self.is_flush():
            if self.is_straight():
                self.rank = HandRanking.STRAIGHT_FLUSH
            else:
                self.rank = HandRanking.FLUSH
        elif self.is_straight():
            self.rank = HandRanking.STRAIGHT
        elif duplicates:
            if len(duplicates) == 2:
                if len(duplicates[1]) == 3:
                    self.rank = HandRanking.FULL_HOUSE
                else:
                    self.rank = HandRanking.TWO_PAIR
            else:
                if len(duplicates[0]) == 4:
                    self.rank = HandRanking.FOUR_OF_KIND
                elif len(duplicates[0]) == 3:
                    self.rank = HandRanking.THREE_OF_KIND
                else:
                    self.rank = HandRanking.PAIR
            self.rearrange_duplicates(duplicates)
        else:
            self.rank = HandRanking.HIGH_CARD

    def __lt__(self, other):
        if self.rank < other.rank:
            return True
        if self.rank > other.rank:
            return False
        for self_card, other_card in zip(self.cards[::-1], other.cards[::-1]):
            if self_card < other_card:
                return True
            elif self_card > other_card:
                return False
        return False

    def __eq__(self, other):
        if self.rank != other.rank:
            return False
        for self_card, other_card in zip(self.cards, other.cards):
            if self_card != other_card:
                return False
        return True

    def rearrange_duplicates(self, duplicates):
        flat_duplicates = [card for _cards in duplicates for card in _cards]
        for dup in flat_duplicates:
            self.cards.pop(self.cards.index(dup))
        self.cards += flat_duplicates

    def is_straight(self):
        ranks = [RANK_INFO[card.rank]["value"] for card in self.cards]
        for i in range(1, 5):
            if ranks[i - 1] != ranks[i] - 1:
                break
        else:
            return True
        if ranks == [0, 1, 2, 3, 12]:
            self.cards = [self.cards[-1]] + self.cards[:-1]
            return True
        return False

    def is_flush(self):
        suit = self.cards[0].suit
        for card in self.cards[1:]:
            if card.suit != suit:
                return False
        return True

    def get_duplicates(self):
        duplicates = []
        cur_duplicate = [self.cards[0]]
        for card in self.cards[1:]:
            if cur_duplicate[0] != card:
                if len(cur_duplicate) > 1:
                    duplicates.append(cur_duplicate)
                cur_duplicate = [card]
            else:
                cur_duplicate.append(card)
        if len(cur_duplicate) > 1:
            duplicates.append(cur_duplicate)
        if len(duplicates) == 2 and len(duplicates[0]) > len(duplicates[1]):
            duplicates[0], duplicates[1] = duplicates[1], duplicates[0]
        return duplicates


def best_possible_hand(public, private):
    return max(Hand(list(hand)) for hand in combinations(public + private, 5))


class PokerGameView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @nextcord.ui.button(label="Начать раздачу", style=nextcord.ButtonStyle.green)
    async def start_distribution(self, interaction: Interaction):
        member = interaction.user
        guild = interaction.guild
        message = interaction.message
        embed = message.embeds[0]

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

        old_field_value = "\n".join(embed.fields[3].value.split("\n")[:4])
        min_bet = int(embed.fields[5].value.split("\n")[4].split()[0])
        next_player_id, next_player = await get_next_player(min_bet, active_players[str(message.id)], guild)
        embed.set_field_at(3, name="\u200b",
                           value=f"{old_field_value}\n"
                                 f"{next_player_id}.\t{next_player}\n",
                           inline=True)

        await interaction.send("Раздача завершена!")
        # await message.edit(embed=embed,
        #                    components=[Button(style=ButtonStyle.gray, label="Посмотреть свои карты")])

        await commit_changes(active_card_decks, "game_data/active_card_decks.json")
        await commit_changes(active_players, "game_data/active_players.json")


class PokerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(guild_ids=TEST_GUILDS_ID, description="test")
    async def poker(self, interaction: Interaction):
        pass

    @poker.subcommand(
        description="Информация о правилах игры покер и о взаимодействии с ботом."
    )
    async def help(self, interaction: Interaction):
        await interaction.send("**ПРАВИЛА ИГРЫ В ТЕХАССКИЙ ХОЛДЕМ**\n"
                               "/play - начать игру в созданном лобби\n"
                               "/bet [размер ставки] - сделать ставку во время раунда\n"
                               "/check - пропустить ход, если ваша ставка равна минимальной\n"
                               "/raise [размер повышения] - повысить ставку\n"
                               "/reraise [размер второго повышения] - повторно повысить ставку "
                               "(работает только полсе /raise)\n"
                               "/call - поддержать ставку\n\n"
                               "**ИНСТРУКЦИЯ ДЛЯ НАЧАЛА ИГРЫ:**\n"
                               "С помощью команды */start_poker_session* Вы создаёте спеациальное "
                               "лобби для игры в покер\n"
                               "Для начала новой игры, нужно написать /start_new_round"
                               "Для того, чтобы покинуть лобби нужно написать команду /leave\n"
                               "\t**ВАЖНО!** Если Вы участвуйте в игре, */leave* не будет работать, "
                               "лучше всего воспользоваться командой */fold*, а уже затем */leave*\n\n"
                               "**Дополнительная информация по игре:**")
        await interaction.send("https://s1.studylib.ru/store/data/002146921_1-a1da1e4905ce29101b5da0116d42a333.png")

    @poker.subcommand(description="t")
    async def start(
            self,
            interaction: Interaction,
            members: str = SlashOption(
                description="Игроки, участвующие в игре. Совет! Просто упомените "
                            "всех игроков в покер (от 2 до 5 человек)",
                required=True
            ),
            bet: int = SlashOption(
                description="Плата за вход в игру и размер обязательной ставки (минимум - 10)",
                required=True
            ),
            time: int = SlashOption(
                description="Время (в часах), через которое удалится лобби покера "
                            "(от 1 часа до 12 часов)",
                required=True
            )
    ):
        guild = interaction.guild
        raw_member_data = members.split("><")
        members = [guild.get_member(await clean_member_id(member_id)) for member_id in raw_member_data]
        author = interaction.user
        if author not in members:
            members.append(author)

        # user_balance = db_sess.query(User).filter(User.id == f"{ctx.author.id}-{guild.id}").first().balance
        # try:
        #     if int(bet) < 10:
        #         raise IncorrectBetAmount(f"- Нельзя ставить ставку, которая меньше минимальной (10 Gaudium)")
        #     if int(bet) > user_balance:
        #         raise IncorrectBetAmount(f"- Ставка {bet} Gaudium не может быть применена, "
        #                                  f"так как у Вас нет достаточной суммы.\n"
        #                                  f"Ваш баланс: {user_balance} Gaudium")
        # except TypeError:
        #     raise IncorrectBetValue("- Размер ставки может быть ТОЛЬКО целым числом!")
        #
        # try:
        #     if not (1 < int(time) < 12):
        #         raise InvalidTimeAmount("- Время, через которое удалится лобби может быть от 1 часа до 12 часов!")
        # except TypeError:
        #     raise IncorrectTimeValue("- Время существования лобби покера может быть ТОЛЬКО целым числом!")
        #
        # if "таверна" not in ctx.channel.name:
        #     raise ChannelNameError(f"- Эта команда работает только в тавернах разных городов.\n"
        #                            f"В канале {ctx.channel} эту команду использовать нельзя!")
        # if not 2 <= len(members) <= 5:
        #     raise IncorrectMemberAmount(f"- Неверное количество игроков!\n"
        #                                 f"Для игры в покер нужно от 2 до 5 человек. У вас - {len(members)}.")
        #
        # for member in members:
        #     if member.bot:
        #         raise IncorrectUser(f"- Выбран неверный пользователь.\n{member.name} - бот!")
        #     if get(guild.roles, name="Игрок") not in member.roles:
        #         raise IncorrectUser(f"- Выбран неверный пользователь.\nУ {member.name} нет роли \"Игрок\"!")

        channel_name = f"poker-lobby-{''.join(filter(str.isalnum, author.name))}".lower()
        channel = get(guild.channels, name=channel_name)
        if channel:
            await channel.delete()

        channel = await guild.create_text_channel(channel_name, category=interaction.channel.category)

        await channel.set_permissions(guild.default_role, send_messages=False, read_messages=False)
        for member in members:
            await channel.set_permissions(member, send_messages=True, read_messages=True)

        games_history = json.load(open("game_data/games_history.json"))
        games_history[str(channel.id)] = 0

        members_list = "\n".join([member.mention for member in members])
        value_emoji = self.bot.get_emoji(EMOJIS_ID["Валюта"])
        await interaction.send(f"Лобби {channel.mention} создано.\n{members_list}")
        message = await channel.send(f"**ЖДЁМ НАЧАЛА ИГРЫ!**\n"
                                     f"Чтобы принять участие в партии покера, нажмите кнопку ✅\n"
                                     f"*NB! Для игры, нужно иметь, минимум {bet} {value_emoji}*\n"
                                     f"**__Текущие участники:__**\n"
                                     f"᲼᲼᲼Отсутствуют :(")
        await message.add_reaction("✅")
        await message.pin()

        await commit_changes(games_history, "game_data/games_history.json")

        if int(time) > 1:
            await asyncio.sleep((time - 1) * 60 * 60)
            await channel.send("**Данный канал удалится через 1 час**")

        await asyncio.sleep(60 * 60)
        await channel.delete()

    @commands.command()
    async def play(self, interaction: Interaction):
        guild = interaction.guild
        channel = interaction.channel

        # if "poker-lobby" not in channel.name:
        #     raise ChannelNameError("- Эту команду можно использовать только в лобби покера!")

        pins = channel.pins()
        message_text = pins[-1].content

        games_history = json.load(open("game_data/games_history.json"))

        bet = int(message_text.split("\n")[2].split()[6])
        members_ids = [await clean_member_id(member.split("  ")[-1]) for member in message_text.split("\n")[4:]]
        members = [guild.get_member(member_id) for member_id in members_ids]
        value_emoji = self.bot.get_emoji(EMOJIS_ID["Валюта"])

        games_count = games_history[str(channel.id)]
        dealer_id = games_count if games_count < len(members) else games_count % len(members)
        dealer = members[dealer_id]

        small_blind_id = dealer_id + 1 if dealer_id + 1 < len(members) else (dealer_id + 1) % len(members)
        blind_id = dealer_id + 2 if dealer_id + 2 < len(members) else (dealer_id + 2) % len(members)

        db_sess.query(User).filter(User.id == f"{members_ids[small_blind_id]}-{guild.id}").first().balance -= bet // 2
        db_sess.query(User).filter(User.id == f"{members_ids[blind_id]}-{guild.id}").first().balance -= bet

        embed = nextcord.Embed(title=f"Партия в покер в процессе", color=0x99d98c)

        members_text = await self.get_formatted_players(members, guild.id, value_emoji)

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
                              f"**Минимум для ставки:**\n"
                              f"{bet} {value_emoji}",
                        inline=True)

        embed.add_field(name="\u200b", value="**Открытые карты:**\n"
                                             "Отсутствуют", inline=True)
        embed.add_field(name="\u200b", value=f"**Последнее действие:**\n"
                                             f"Собраны блайнды с игроков:\n"
                                             f"  {members[small_blind_id]} {round(bet * 0.5)} {value_emoji}\n"
                                             f"  {members[blind_id]} {bet} {value_emoji}", inline=True)

        # await pins[0].unpin()
        message = await interaction.send(embed=embed, view=PokerGameView())
        await message.pin()

        active_players = json.load(open("game_data/active_players.json", encoding="utf8"))

        games_history[str(channel.id)] += 1
        active_players[message.id] = {}
        for member_id in members_ids:
            active_players[message.id][member_id] = {"deck": [], "bet": 0, "action": ""}

        active_players[message.id][members_ids[small_blind_id]]["bet"] = bet // 2
        active_players[message.id][members_ids[blind_id]]["bet"] = bet

        await commit_changes(games_history, "game_data/games_history.json")
        await commit_changes(active_players, "game_data/active_players.json")
        db_sess.commit()

    async def poker_win(self, ctx, pot, message_id=None, opened_cards=None, last_player_id=None):
        guild = ctx.guild
        value_emoji = self.bot.get_emoji(EMOJIS_ID["Валюта"])

        if last_player_id:
            user = db_sess.query(User).filter(User.id == f"{last_player_id}-{guild.id}").first()
            user.balance += pot
            db_sess.commit()
            await ctx.send(f"{guild.get_member(int(last_player_id))} выиграл и заработал {pot} {value_emoji}!")
            return

        active_players = json.load(open("game_data/active_players.json", encoding="utf8"))[str(message_id)]

        players_ids = []
        all_players_cards = {}
        for player_id, player_info in active_players.items():
            for card in player_info["deck"]:
                value, suit = card.split(" - ")
                if all_players_cards.get(player_id, "") == "":
                    all_players_cards[player_id] = [Card(suit, value)]
                else:
                    all_players_cards[player_id].append(Card(suit, value))

            players_ids.append(player_id)

        all_opened_cards = []
        for card in opened_cards:
            value, suit = card.split()
            all_opened_cards.append(Card(suit.split(":")[1].capitalize(), value))

        winners = []
        best_hand = None
        for player_id in players_ids:
            hand = best_possible_hand(all_players_cards[player_id], all_opened_cards)
            if best_hand is None or hand > best_hand:
                winners = [player_id]
                best_hand = hand
            elif hand == best_hand:
                winners.append(player_id)

        for winner in winners:
            user = db_sess.query(User).filter(User.id == f"{winner}-{guild.id}").first()
            user.balance += pot // len(winners)

            await ctx.send(f"{guild.get_member(int(winner)).mention} выиграл и "
                           f"заработал {pot // len(winners)} {value_emoji}!")

        db_sess.commit()

    @staticmethod
    async def get_all_next_players(current_bet, members_data):
        next_players = []
        for member_data in members_data.values():
            if member_data["bet"] < current_bet and member_data["action"] != "all-in":
                next_players.append("player")

        return len(next_players)

    @staticmethod
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

    async def start_new_round(self, round_num, message):
        deck = DeckOfCards()
        cards_data = json.load(open("game_data/active_card_decks.json", encoding="utf8"))
        deck.cards = cards_data[str(message.id)]
        embed = message.embeds[0]

        amount_to_take = 3 if round_num == 2 else 1
        old_cards_value = ""
        if round_num != 2:
            old_cards_value = "\n".join(embed.fields[6].value.split("\n")[1:])
            old_cards_value = f"{old_cards_value}\n"
        text_cards = []
        for card_info in await deck.take(amount_to_take):
            value, suit = card_info.split(" - ")
            text_cards.append(f"{value} {self.bot.get_emoji(playing_cards_emoji[suit])}")
        text_cards = "\n".join(text_cards)

        embed.set_field_at(6, name="\u200b",
                           value=f"**Открытые карты:**\n"
                                 f"{old_cards_value}"
                                 f"{text_cards}")
        embed.set_field_at(7, name="\u200b",
                           value="**Последнее действие:**\n"
                                 "Начался новый раунд!")

        await message.edit(embed=embed)
        cards_data[str(message.id)] = deck.cards
        await commit_changes(cards_data, "game_data/active_card_decks.json")

    async def commit_game_changes(self, ctx, message, data, guild):
        value_emoji = self.bot.get_emoji(EMOJIS_ID["Валюта"])
        embed = message.embeds[0]

        old_third_field_value = "\n".join(embed.fields[3].value.split("\n")[:4])

        all_active_members = json.load(open("game_data/active_players.json", encoding="utf8"))
        members = [guild.get_member(int(member_id))
                   for member_id in list(all_active_members[str(message.id)].keys())]
        members_text = await self.get_formatted_players(members, guild.id, value_emoji)

        embed.set_field_at(0, name="\u200b", value="\n\n".join(members_text[0]), inline=True)
        embed.set_field_at(1, name="\u200b", value="\u200b", inline=True)
        embed.set_field_at(2, name="\u200b", value="\n\n".join(members_text[1]), inline=True)

        if not data["next_player"]:
            opened_cards = embed.fields[6].value.split("\n")[1:]
            round_num = len(opened_cards) if len(opened_cards) > 1 else len(opened_cards) + 1

            if round_num > 4:
                await self.poker_win(ctx, data['new_pot'], message_id=message.id, opened_cards=opened_cards)
                return

            active_players = json.load(open("game_data/active_players.json", encoding="utf8"))

            for player_id in active_players[str(message.id)].keys():
                active_players[str(message.id)][player_id]["bet"] = 0

                if active_players[str(message.id)][player_id]["action"] != "all-in":
                    active_players[str(message.id)][player_id]["action"] = ""

            await commit_changes(active_players, "game_data/active_players.json")

            next_player_id, next_player = await get_next_player(data["new_min_bet"],
                                                                active_players[str(message.id)],
                                                                guild)

            embed.set_field_at(3, name="\u200b",
                               value=f"{old_third_field_value}\n"
                                     f"{next_player_id}.\t{next_player}\n",
                               inline=True)
            embed.set_field_at(5, name="\u200b",
                               value=f"**Общий куш:**\n"
                                     f"{data['new_pot']} {value_emoji}\n\n"
                                     f"**Минимальная ставка:**\n"
                                     f"0 {value_emoji}")

            await self.start_new_round(round_num, message)
            return

        embed.set_field_at(3, name="\u200b",
                           value=f"{old_third_field_value}\n"
                                 f"{data['next_player_id']}.\t{data['next_player']}",
                           inline=True)

        embed.set_field_at(5, name="\u200b",
                           value=f"**Общий куш:**\n"
                                 f"{data['new_pot']} {value_emoji}\n\n"
                                 f"**Минимальная ставка:**\n"
                                 f"{data['new_min_bet']} {value_emoji}")

        if data["last_action"] != "":
            embed.set_field_at(7, name="\u200b",
                               value=f"**Последнее действие:**\n"
                                     f"{data['last_action']}")

        await message.edit(embed=embed)

    @staticmethod
    async def get_current_game_data(interaction: Interaction):
        pins = await interaction.channel.pins()
        current_game_message = None
        for pin_message in pins:
            if pin_message.embeds and "Партия в покер в процессе" == pin_message.embeds[0].title:
                current_game_message = pin_message
                break

        if not current_game_message:
            return

        current_game_data = {}

        embed = current_game_message.embeds[0]

        raw_bet_data = embed.fields[5].value.split("\n")

        current_player_line = embed.fields[3].value.split("\n")[4]
        current_player_name, current_player_desc = " ".join(current_player_line.split()[1:]).split("#")

        current_game_data["message"] = current_game_message
        current_game_data["previous_action"] = embed.fields[-1].value.split("\n")[1]

        current_game_data["pot"] = int(raw_bet_data[1].split()[0])
        current_game_data["min_bet"] = int(raw_bet_data[4].split()[0])

        current_game_data["current_player"] = get(interaction.guild.members,
                                                  name=current_player_name,
                                                  discriminator=current_player_desc)

        return current_game_data


async def get_next_player(current_bet, members_data, guild):
    next_player = None
    next_player_id = -1
    members_all_in = 0
    for member_id, member_data in members_data.items():
        if (current_bet == 0 and member_data["action"] != "check" or member_data["bet"] < current_bet) \
                and member_data["action"] != "all-in":
            next_player_id = list(members_data.keys()).index(member_id) + 1
            next_player = guild.get_member(int(member_id))
            break
        if member_data["action"] == "all-in":
            members_all_in += 1

    if len(list(members_data.keys())) == members_all_in:
        return -1, None
    return next_player_id, next_player


def setup(bot):
    bot.add_cog(PokerCog(bot))
