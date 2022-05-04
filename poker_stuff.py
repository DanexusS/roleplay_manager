import json
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

cards = json.load(open("cards.json", encoding="utf8"))


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


class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

    def __lt__(self, other):
        return RANK_INFO[self.rank]["value"] < RANK_INFO[other.rank]["value"]

    def __eq__(self, other):
        return self.rank == other.rank


class Deck:
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
            taken_card = choice(self.cards)

            taken_cards.append(taken_card)
            self.cards.remove(taken_card)
            shuffle(self.cards)

        return taken_cards


class OnTheHand:
    def __init__(self, _cards):
        self.cards = sorted(_cards)

        dups = self.get_dups()

        if self.is_flush():
            if self.is_straight():
                self.rank = HandRanking.STRAIGHT_FLUSH
            else:
                self.rank = HandRanking.FLUSH
        elif self.is_straight():
            self.rank = HandRanking.STRAIGHT
        elif dups:
            if len(dups) == 2:
                if len(dups[1]) == 3:
                    self.rank = HandRanking.FULL_HOUSE
                else:
                    self.rank = HandRanking.TWO_PAIR
            else:
                if len(dups[0]) == 4:
                    self.rank = HandRanking.FOUR_OF_KIND
                elif len(dups[0]) == 3:
                    self.rank = HandRanking.THREE_OF_KIND
                else:
                    self.rank = HandRanking.PAIR
            self.rearrange_dups(dups)
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

    def rearrange_dups(self, dups):
        flat_dups = [card for _cards in dups for card in _cards]
        for dup in flat_dups:
            self.cards.pop(self.cards.index(dup))
        self.cards += flat_dups

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

    def get_dups(self):
        dups = []
        cur_dup = [self.cards[0]]
        for card in self.cards[1:]:
            if cur_dup[0] != card:
                if len(cur_dup) > 1:
                    dups.append(cur_dup)
                cur_dup = [card]
            else:
                cur_dup.append(card)
        if len(cur_dup) > 1:
            dups.append(cur_dup)
        if len(dups) == 2 and len(dups[0]) > len(dups[1]):
            dups[0], dups[1] = dups[1], dups[0]
        return dups


def best_possible_hand(public, private):
    return max(OnTheHand(list(hand)) for hand in combinations(public + private, 5))