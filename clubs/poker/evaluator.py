"""Classes and functions to evaluate poker hands"""
import functools
import itertools
import operator
from timeit import default_timer as timer
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

from clubs import error

from . import card


class Evaluator(object):
    """Evalutes poker hands using hole and community cards

    Parameters
    ----------
    suits : int
        number of suits in deck
    ranks : int
        number of ranks in deck
    cards_for_hand : int
        number of cards used for valid poker hand
    mandatory_hole_cards : int, optional
        number of hole cards which must be used for a hands, by default
        0
    low_end_straight : bool, optional
        toggle to include the low ace straight within valid hands, by
        default True
    order : List[str], optional
        optional custom order of hand ranks, must be permutation of
        ['sf', 'fk', 'fh', 'fl', 'st', 'tk', 'tp', 'pa', 'hc']. if
        order=None, hands are ranked by rarity. by default None
    """

    def __init__(
        self,
        suits: int,
        ranks: int,
        cards_for_hand: int,
        mandatory_hole_cards: int = 0,
        low_end_straight: bool = True,
        order: Optional[List[str]] = None,
    ):

        if cards_for_hand < 1 or cards_for_hand > 5:
            raise error.InvalidHandSizeError(
                f"Evaluation for {cards_for_hand} "
                f"card hands is not supported. "
                f"clubs currently supports 1-5 card poker hands"
            )

        self.suits = suits
        self.ranks = ranks
        self.cards_for_hand = cards_for_hand
        self.mandatory_hole_cards = mandatory_hole_cards

        self.table = LookupTable(
            suits, ranks, cards_for_hand, low_end_straight=low_end_straight, order=order
        )

        total = sum(
            self.table.hand_dict[hand]["suited"] for hand in self.table.ranked_hands
        )

        hands = [
            "{} ({:.4%})".format(hand, self.table.hand_dict[hand]["suited"] / total)
            for hand in self.table.ranked_hands
        ]
        self.hand_ranks = " > ".join(hands)

    def __str__(self) -> str:
        return self.hand_ranks

    def __repr__(self) -> str:
        return f"Evaluator ({id(self)}): {str(self)}"

    def evaluate(
        self, hole_cards: List[card.Card], community_cards: List[card.Card]
    ) -> int:
        """Evaluates the hand rank of a poker hand from a list of hole
        and a list of community cards. Empty hole and community cards
        are supported as well as requiring a minimum number of hole
        cards to be used.

        Parameters
        ----------
        hole_cards : List[card.Card]
            list of hole cards
        community_cards : List[card.Card]
            list of community cards

        Returns
        -------
        int
            hand rank
        """
        # if a number of hole cards are mandatory
        if self.mandatory_hole_cards:
            # get all hole and community card combinations
            hole_card_combs = itertools.combinations(
                hole_cards, self.mandatory_hole_cards
            )
            num_comm_cards = self.cards_for_hand - self.mandatory_hole_cards
            if num_comm_cards:
                comm_card_combs = itertools.combinations(
                    community_cards, num_comm_cards
                )
                iterator = itertools.product(hole_card_combs, comm_card_combs)
                all_card_combs = list((sum(card_comb, ()) for card_comb in iterator))
            else:
                all_card_combs = list(hole_card_combs)
        # else create combinations from all cards
        else:
            all_card_combs = list(
                itertools.combinations(
                    hole_cards + community_cards, self.cards_for_hand
                )
            )

        minimum = self.table.max_rank

        for card_comb in all_card_combs:
            score = self.table.lookup(list(card_comb))
            if score < minimum:
                minimum = score
        return minimum

    def get_rank_class(self, hand_rank: int) -> str:
        """Outputs hand rank string from integer hand rank

        Parameters
        ----------
        hand_rank : int
            hand_rank (int): integer hand rank

        Returns
        -------
        str
            hand rank string
        """
        if hand_rank < 0:
            raise error.InvalidHandRankError(
                (
                    f"invalid hand rank, expected 0 <= hand_rank"
                    f" <= {self.table.max_rank}, got {hand_rank}"
                )
            )
        for hand in self.table.ranked_hands:
            if hand_rank <= self.table.hand_dict[hand]["cumulative unsuited"]:
                return hand
        raise error.InvalidHandRankError(
            (
                f"invalid hand rank, expected 0 <= hand_rank"
                f" <= {self.table.max_rank}, got {hand_rank}"
            )
        )

    def speed_test(self, n: int = 100000) -> float:
        """Tests speed of evaluator

        Parameters
        ----------
        n : int, optional
            number of iterations/hands to test, by default 100000

        Returns
        -------
        float
            average time per hand evaluation
        """
        deck = card.Deck(self.suits, self.ranks)

        time = 0.0
        for _ in range(n):
            start = timer()
            self.evaluate(deck.draw(2), deck.draw(5))
            time += timer() - start

        avg = time / n
        return avg


class LookupTable:
    """Lookup table maps unique prime product of hands to unique
    integer hand rank. The lower the rank the better the hand

    Parameters
    ----------
    suits : int
        number of suits in deck
    ranks : int
        number of ranks in deck
    cards_for_hand : int
        number of cards used for a poker hand
    low_end_straight : bool, optional
        toggle to include straights where ace is the lowest card, by
        default True
    order : Optional[List[str]], optional
        custom hand rank order, if None hands are ranked by rarity, by
        default None
    """

    ORDER_STRINGS = ["sf", "fk", "fh", "fl", "st", "tk", "tp", "pa", "hc"]

    def __init__(
        self,
        suits: int,
        ranks: int,
        cards_for_hand: int,
        low_end_straight: bool = True,
        order: Optional[List[str]] = None,
    ):

        if order is not None:
            if any(string not in order for string in self.ORDER_STRINGS):
                raise error.InvalidOrderError(
                    (
                        f"invalid order list {order},"
                        f"order list must be permutation of {self.ORDER_STRINGS}"
                    )
                )

        # number of suited and unsuited possibilities of different hands
        straight_flushes, u_straight_flushes = self._straight_flush(
            suits, ranks, cards_for_hand, low_end_straight
        )
        four_of_a_kinds, u_four_of_a_kinds = self._four_of_a_kind(
            suits, ranks, cards_for_hand
        )
        full_houses, u_full_houses = self._full_house(suits, ranks, cards_for_hand)
        flushes, u_flushes = self._flush(suits, ranks, cards_for_hand, low_end_straight)
        straights, u_straights = self._straight(
            suits, ranks, cards_for_hand, low_end_straight
        )
        three_of_a_kinds, u_three_of_a_kinds = self._three_of_a_kind(
            suits, ranks, cards_for_hand
        )
        two_pairs, u_two_pairs = self._two_pair(suits, ranks, cards_for_hand)
        pairs, u_pairs = self._pair(suits, ranks, cards_for_hand)
        high_cards, u_high_cards = self._high_card(
            suits, ranks, cards_for_hand, low_end_straight
        )

        self.hand_dict = {
            "straight flush": {
                "suited": straight_flushes,
                "unsuited": u_straight_flushes,
            },
            "four of a kind": {
                "suited": four_of_a_kinds,
                "unsuited": u_four_of_a_kinds,
            },
            "full house": {"suited": full_houses, "unsuited": u_full_houses},
            "flush": {"suited": flushes, "unsuited": u_flushes},
            "straight": {"suited": straights, "unsuited": u_straights},
            "three of a kind": {
                "suited": three_of_a_kinds,
                "unsuited": u_three_of_a_kinds,
            },
            "two pair": {"suited": two_pairs, "unsuited": u_two_pairs},
            "pair": {"suited": pairs, "unsuited": u_pairs},
            "high card": {"suited": high_cards, "unsuited": u_high_cards},
        }

        # suited hands
        s_hands = [
            (straight_flushes, "straight flush"),
            (four_of_a_kinds, "four of a kind"),
            (full_houses, "full house"),
            (flushes, "flush"),
            (straights, "straight"),
            (three_of_a_kinds, "three of a kind"),
            (two_pairs, "two pair"),
            (pairs, "pair"),
            (high_cards, "high card"),
        ]

        # sort suited hands and rank unsuited hands by suited
        # rank order or by order provided
        if order is None:
            s_hands = sorted(s_hands)
        else:
            idcs = [self.ORDER_STRINGS.index(hand) for hand in order]
            s_hands = [s_hands[idx] for idx in idcs]
        # lookup is done on unsuited hands but hand
        # rank is dependent on suited hands
        u_hands = [
            (self.hand_dict[u_hand[1]]["unsuited"], u_hand[1]) for u_hand in s_hands
        ]

        # compute cumulative number of unsuited hands for each hand
        # cumulative unsuited is the maximum rank a hand can have
        ranked_hands = []
        rank = 0
        cumulative_hands = 0
        for u_hand in u_hands:
            hand_rank = u_hand[1]
            cumulative_hands += u_hand[0]
            self.hand_dict[hand_rank]["cumulative unsuited"] = cumulative_hands
            if cumulative_hands > 0:
                self.hand_dict[hand_rank]["rank"] = rank
                rank += 1
                ranked_hands.append(hand_rank)
        self.max_rank = cumulative_hands

        # list of hands ordered by rank from best to worst
        self.ranked_hands = ranked_hands

        # create lookup tables
        suited_lookup, unsuited_lookup = self._flushes(
            ranks, cards_for_hand, low_end_straight
        )
        unsuited_lookup = self._multiples(ranks, cards_for_hand, unsuited_lookup)

        # if suited hands aren't relevant set the suited
        # lookup table equal to the unsuited table
        if not self.hand_dict["flush"]["cumulative unsuited"]:
            suited_lookup = unsuited_lookup

        self.suited_lookup = suited_lookup
        self.unsuited_lookup = unsuited_lookup

    def lookup(self, cards: List[card.Card]) -> int:
        """Return unique hand rank for list of cards

        Parameters
        ----------
        cards : List[card.Card]
            list of cards to be evaluated

        Returns
        -------
        int
            hand rank
        """
        # if all flush bits equal then use flush lookup
        if functools.reduce(operator.and_, cards, 0xF000):
            hand_or = functools.reduce(operator.or_, cards) >> 16
            prime = _prime_product_from_rank_bits(hand_or)
            return self.suited_lookup[prime]
        prime = _prime_product_from_hand(cards)
        return self.unsuited_lookup[prime]

    @staticmethod
    def _straight_flush(
        suits: int, ranks: int, cards_for_hand: int, low_end_straight: bool
    ) -> Tuple[int, int]:
        if cards_for_hand < 3 or suits < 2:
            return 0, 0
        # number of smallest cards which start straight
        unsuited = ranks - (cards_for_hand - 1) + low_end_straight
        # multiplied with number of suits
        suited = max(unsuited, unsuited * suits)
        return int(suited), int(unsuited)

    @staticmethod
    def _four_of_a_kind(suits: int, ranks: int, cards_for_hand: int) -> Tuple[int, int]:
        if cards_for_hand < 4 or suits < 4:
            return 0, 0
        # choose 1 rank for quads multiplied by
        # rank choice for remaining cards
        unsuited = _ncr(ranks, 1) * _ncr(ranks - 1, cards_for_hand - 4)
        # mutliplied with number of suit choices for remaining cards
        suited = max(unsuited, unsuited * suits ** (cards_for_hand - 4))
        return int(suited), int(unsuited)

    @staticmethod
    def _full_house(suits: int, ranks: int, cards_for_hand: int) -> Tuple[int, int]:
        if cards_for_hand < 5 or suits < 3:
            return 0, 0
        # choose one rank for trips and pair multiplied by
        # rank choice for remaining cards
        unsuited = (
            _ncr(ranks, 1) * _ncr(ranks - 1, 1) * _ncr(ranks - 2, cards_for_hand - 5)
        )
        # multiplied with number of suit choices for
        # trips + pair and remaining cards
        suited = max(
            unsuited,
            unsuited * _ncr(suits, 3) * _ncr(suits, 2) * suits ** (cards_for_hand - 5),
        )
        return int(suited), int(unsuited)

    @staticmethod
    def _flush(
        suits: int, ranks: int, cards_for_hand: int, low_end_straight: bool
    ) -> Tuple[int, int]:
        if cards_for_hand < 3 or suits < 2:
            return 0, 0
        # all straight combinations
        straight_flushes = ranks - (cards_for_hand - 1) + low_end_straight
        # choose all cards from ranks minus straight flushes
        unsuited = _ncr(ranks, cards_for_hand) - straight_flushes
        # multiplied by number of suits
        suited = max(unsuited, unsuited * suits)
        return int(suited), int(unsuited)

    @staticmethod
    def _straight(
        suits: int, ranks: int, cards_for_hand: int, low_end_straight: bool
    ) -> Tuple[int, int]:
        if cards_for_hand < 3:
            return 0, 0
        # number of smallest cards which start straight
        unsuited = ranks - (cards_for_hand - 1) + low_end_straight
        # straight flush combinations
        straight_flushes = 0
        if suits > 1:
            straight_flushes = unsuited * suits
        # multiplied with suit choice for every card
        # minus straight flushes
        suited = max(unsuited, unsuited * suits ** cards_for_hand - straight_flushes)
        if suits < 2:
            suited = unsuited
        return int(suited), int(unsuited)

    @staticmethod
    def _three_of_a_kind(
        suits: int, ranks: int, cards_for_hand: int
    ) -> Tuple[int, int]:
        if cards_for_hand < 3 or suits < 3:
            return 0, 0
        # choose one rank for trips multiplied by
        # rank choice for remaining cards
        unsuited = _ncr(ranks, 1) * _ncr(ranks - 1, cards_for_hand - 3)
        # multiplied with suit choices for trips and remaining cards
        suited = max(
            unsuited, unsuited * _ncr(suits, 3) * _ncr(suits, 3) ** (cards_for_hand - 3)
        )
        return int(suited), int(unsuited)

    @staticmethod
    def _two_pair(suits: int, ranks: int, cards_for_hand: int) -> Tuple[int, int]:
        if cards_for_hand < 4 or suits < 2:
            return 0, 0
        # choose two ranks for pairs multiplied by
        # ranks for remaining cards
        unsuited = _ncr(ranks, 2) * _ncr(ranks - 2, cards_for_hand - 4)
        # multiplied with suit choices for both pairs
        # and suit choices for remaining cards
        suited = max(
            unsuited, unsuited * _ncr(suits, 2) ** 2 * suits ** (cards_for_hand - 4)
        )
        return int(suited), int(unsuited)

    @staticmethod
    def _pair(suits: int, ranks: int, cards_for_hand: int) -> Tuple[int, int]:
        if cards_for_hand < 2 or suits < 2:
            return 0, 0
        # choose rank for pair multiplied by
        # ranks for remaining cards
        unsuited = _ncr(ranks, 1) * _ncr(ranks - 1, cards_for_hand - 2)
        # multiplied with suit choices for pair and remaining cards
        suited = max(
            unsuited, unsuited * _ncr(suits, 2) * suits ** (cards_for_hand - 2)
        )
        return int(suited), int(unsuited)

    @staticmethod
    def _high_card(
        suits: int, ranks: int, cards_for_hand: int, low_end_straight: bool
    ) -> Tuple[int, int]:
        # number of smallest cards which start straight
        straights = 0
        if cards_for_hand > 2:
            straights = ranks - (cards_for_hand - 1) + low_end_straight
        # any combination of rank and subtract straights
        unsuited = _ncr(ranks, cards_for_hand) - straights
        # multiplied with suit choices for all cards
        # all same suits not allowed
        suited = max(unsuited, unsuited * (suits ** cards_for_hand - suits))
        if suits < 2:
            suited = unsuited
        return int(suited), int(unsuited)

    @staticmethod
    def _gen_straight_flush(
        cards_for_hand: int, ranks: int, low_end_straight: bool
    ) -> List[int]:
        straight_flushes = []
        # start with best straight (flush)
        # for 5 card hand with 13 ranks: 0b1111100000000
        bin_num_str = "0b" + "1" * cards_for_hand + "0" * (13 - cards_for_hand)
        # remove one 0 for every straight (flush)
        for _ in range(ranks - (cards_for_hand - 1)):
            straight_flushes.append(int(bin_num_str, 2))
            bin_num_str = bin_num_str[:-1]
        if low_end_straight:
            # add low end straight
            bin_num_str = (
                "0b1"
                + "0" * (ranks - cards_for_hand)
                + "1" * (cards_for_hand - 1)
                + "0" * (13 - ranks)
            )
            straight_flushes.append(int(bin_num_str, 2))

        return straight_flushes

    @staticmethod
    def _gen_flush(
        cards_for_hand: int, ranks: int, straight_flushes: List[int]
    ) -> List[int]:
        flushes = []
        # start with lowest non pair hand
        # for 5 card hand with 13 ranks: 0b11111
        bin_num_str = "0b" + ("1" * cards_for_hand)
        gen = _lexographic_next_bit(int(bin_num_str, 2))
        # iterate over all possibilities of unique hands
        for _ in range(int(_ncr(ranks, cards_for_hand))):
            # pull the next flush pattern from generator
            # offset by number of ranks not in play
            flush = next(gen) << (13 - ranks)
            if flush not in straight_flushes:
                flushes.append(flush)

        flushes.reverse()
        return flushes

    def _flushes(
        self, ranks: int, cards_for_hand: int, low_end_straight: bool
    ) -> Tuple[Dict[int, int], Dict[int, int]]:
        straight_flushes = []
        if (
            self.hand_dict["straight flush"]["cumulative unsuited"]
            or self.hand_dict["straight"]["cumulative unsuited"]
        ):
            straight_flushes = self._gen_straight_flush(
                cards_for_hand, ranks, low_end_straight
            )
        # dynamically generate all the other
        # flushes (including straight flushes)
        flushes = []
        if (
            self.hand_dict["flush"]["cumulative unsuited"]
            or self.hand_dict["high card"]["cumulative unsuited"]
        ):
            flushes = self._gen_flush(cards_for_hand, ranks, straight_flushes)

        def add_to_dict(
            rank_string: str, rank_bits: List[int], lookup: Dict[int, int],
        ) -> Dict[int, int]:
            if not self.hand_dict[rank_string]["cumulative unsuited"]:
                return lookup
            num_ranks = len(rank_bits)
            assert num_ranks == self.hand_dict[rank_string]["unsuited"]
            hand_rank = self._get_rank(rank_string)
            for _rank_bits in rank_bits:
                prime_product = _prime_product_from_rank_bits(_rank_bits)
                lookup[prime_product] = hand_rank
                hand_rank += 1
            return lookup

        suited_lookup: Dict[int, int] = {}
        unsuited_lookup: Dict[int, int] = {}
        suited_lookup = add_to_dict("straight flush", straight_flushes, suited_lookup)
        suited_lookup = add_to_dict("flush", flushes, suited_lookup)
        unsuited_lookup = add_to_dict("straight", straight_flushes, unsuited_lookup)
        unsuited_lookup = add_to_dict("high card", flushes, unsuited_lookup)

        return suited_lookup, unsuited_lookup

    def _multiples(
        self, ranks: int, cards_for_hand: int, unsuited_lookup: Dict[int, int],
    ) -> Dict[int, int]:
        def add_to_dict(
            rank_string: str, multiples: List[int], unsuited_lookup: Dict[int, int],
        ) -> Dict[int, int]:
            # inverse ranks, A - 2
            backwards_ranks = list(range(13 - 1, 13 - 1 - ranks, -1))
            if not self.hand_dict[rank_string]["cumulative unsuited"]:
                return unsuited_lookup
            # get cumulative hand rank
            hand_rank = self._get_rank(rank_string)
            # if different multiples (e.g. full house) order of
            # multiples is important
            if len(set(multiples)) > 1:
                multiple_combinations: Iterable[
                    Tuple[int, ...]
                ] = itertools.permutations(backwards_ranks, len(multiples))
            # if same multiples (e.g. two pair) order of multiples
            # is unimportant
            else:
                multiple_combinations = itertools.combinations(
                    backwards_ranks, len(multiples)
                )
            for card_ranks in multiple_combinations:
                base_product = 1
                # compute product over every combination of multiple
                # card rank
                for card_rank, multiple in zip(card_ranks, multiples):
                    base_product *= card.PRIMES[card_rank] ** multiple
                num_kickers = cards_for_hand - sum(multiples)
                # record product in lookup table
                if num_kickers:
                    kickers = backwards_ranks[:]
                    for card_rank in card_ranks:
                        kickers.remove(card_rank)
                    kicker_combinations = list(
                        itertools.combinations(kickers, num_kickers)
                    )
                    for kickers_tuple in kicker_combinations:
                        product = base_product
                        for kicker in kickers_tuple:
                            product *= card.PRIMES[kicker]
                        unsuited_lookup[product] = hand_rank
                        hand_rank += 1
                else:
                    unsuited_lookup[base_product] = hand_rank
                    hand_rank += 1
            # check hand rank is equal to number of iterated ranks
            num_ranks = hand_rank - self._get_rank(rank_string)
            assert num_ranks == self.hand_dict[rank_string]["unsuited"]

            return unsuited_lookup

        add_to_dict("four of a kind", [4], unsuited_lookup)
        add_to_dict("full house", [3, 2], unsuited_lookup)
        add_to_dict("three of a kind", [3], unsuited_lookup)
        add_to_dict("two pair", [2, 2], unsuited_lookup)
        add_to_dict("pair", [2], unsuited_lookup)

        return unsuited_lookup

    def _get_rank(self, hand: str) -> int:
        rank = self.hand_dict[hand]["rank"]
        if not rank:
            return 0
        better_hand = self.ranked_hands[rank - 1]
        return self.hand_dict[better_hand]["cumulative unsuited"] + 1


def _prime_product_from_rank_bits(rankbits: int) -> int:
    product = 1
    for i in card.INT_RANKS:
        # if the ith bit is set
        if rankbits & (1 << i):
            product *= card.PRIMES[i]
    return product


def _prime_product_from_hand(cards: List[card.Card]) -> int:
    product = 1
    for _card in cards:
        product *= _card & 0xFF
    return product


def _lexographic_next_bit(bits: int) -> Iterator[int]:
    # generator next legographic bit sequence given a bit sequence with
    # N bits set e.g.
    # 00010011 -> 00010101 -> 00010110 -> 00011001 ->
    # 00011010 -> 00011100 -> 00100011 -> 00100101
    lex = bits
    yield lex
    while True:
        temp = (lex | (lex - 1)) + 1
        lex = temp | ((((temp & -temp) // (lex & -lex)) >> 1) - 1)
        yield lex


def _ncr(n: int, r: int) -> int:
    r = min(r, n - r)
    numer = functools.reduce(operator.mul, range(n, n - r, -1), 1)
    denom = functools.reduce(operator.mul, range(1, r + 1), 1)
    return numer // denom
