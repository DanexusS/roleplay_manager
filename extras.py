import json

from consts import cards
from random import shuffle, choice


class DeckOfCards:
    def __init__(self, size=36):
        self.cards = []
        for suit, values in cards.items():
            for value in values[:size // 4]:
                self.cards.append(f"{value} - {suit}")
        self.size = size

    async def shuffle(self):
        shuffle(self.cards)

    async def reset(self):
        self.__init__(self.size)

    async def take(self, amount):
        taken_cards = []
        for number in range(amount):
            taken_card = action(self.cards)

            taken_cards.append(taken_card)
            self.cards.remove(taken_card)
            shuffle(self.cards)

        return taken_cards


async def commit_changes(data, location):
    json.dump(data, open(location, "w", encoding="utf8"), ensure_ascii=False, indent=4)


"""ИСКЛЮЧЕНИЯ"""


class IncorrectUser(Exception):
    pass


class IncompleteTrade(Exception):
    pass


class IncorrectTradeValues(Exception):
    pass


class IncorrectMemberAmount(Exception):
    pass


class IncorrectCityName(Exception):
    pass


class ChannelNameError(Exception):
    pass


class IncorrectBetAmount(Exception):
    pass


class IncorrectGameAction(Exception):
    pass
