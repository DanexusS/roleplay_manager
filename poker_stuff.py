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
