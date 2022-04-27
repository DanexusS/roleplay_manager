from consts import cards
from random import shuffle


class DeckOfCards:
    def __init__(self):
        self.cards = cards

    async def shuffle(self):
        shuffle(self.cards)


"""
    ИСКЛЮЧЕНИЯ
"""


class IncorrectUser(Exception):
    pass


class IncompleteTrade(Exception):
    pass


class IncorrectTradeValues(Exception):
    pass


class IncorrectMemberAmount(Exception):
    pass
