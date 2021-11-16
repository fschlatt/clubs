"""Classes and functions for running poker games"""
import itertools
import operator
from typing import Any, List, Literal, Optional, Tuple, Type, TypedDict, Union

from clubs import error, poker, render


class ObservationDict(TypedDict):
    action: int
    active: List[bool]
    button: int
    call: int
    community_cards: List[poker.Card]
    hole_cards: List[poker.Card]
    max_raise: int
    min_raise: int
    pot: int
    stacks: List[int]
    street_commits: List[int]


class Dealer:
    """Runs a range of different of poker games dependent on the
    given configuration. Supports limit, no limit and pot limit
    bet sizing, arbitrary deck sizes, arbitrary hole and community
    cards and many other options.

    Parameters
    ----------
    num_players : int
        maximum number of players
    num_streets : int
        number of streets including preflop, e.g. for texas hold'em
        num_streets=4
    blinds : Union[int, List[int]]
        blind distribution as a list of ints, one for each player
        starting from the button e.g. [0, 1, 2] for a three player game
        with a sb of 1 and bb of 2, passed ints will be expanded to
        all players i.e. pass blinds=0 for no blinds
    antes : Union[int, List[int]]
        ante distribution as a list of ints, one for each player
        starting from the button e.g. [0, 0, 5] for a three player game
        with a bb ante of 5, passed ints will be expanded to all
        players i.e. pass antes=0 for no antes
    raise_sizes : Union[
            int, Literal["pot", "inf"], List[Union[int, Literal["pot", "inf"]]]
        ]
        max raise sizes for each street, valid raise sizes are ints,
        'inf', and 'pot', e.g. for a 1-2 limit hold'em the raise sizes
        should be [2, 2, 4, 4] as the small and big bet are 2 and 4.
        'inf' can be used for no limit games. pot limit raise
        sizes can be set using 'pot'. if only a single int or
        string is passed the value is expanded to a list the length
        of number of streets, e.g. for a standard no limit game pass
        raise_sizes=float('inf')
    num_raises : Union[int, Literal["inf"], List[Union[int, Literal["inf"]]]]
        max number of bets for each street including preflop, valid
        raise numbers are ints and floats. if only a single int or float
        is passed the value is expanded to a list the length of number
        of streets, e.g. for a standard limit game pass num_raises=4
    num_suits : int
        number of suits to use in deck, must be between 1 and 4
    num_ranks : int
        number of ranks to use in deck, must be between 1 and 13
    num_hole_cards : int
        number of hole cards per player, must be greater than 0
    num_community_cards : Union[int, List[int]]
        number of community cards per street including preflop, e.g.
        for texas hold'em pass num_community_cards=[0, 3, 1, 1]. if only
        a single int is passed, it is expanded to a list the length of
        number of streets
    num_cards_for_hand : int
        number of cards for a valid poker hand, e.g. for texas hold'em
        num_cards_for_hand=5
    mandatory_num_hole_cards : int
        number of hole cards which have to be used for the hand, e.g.
        for pot limit omaha mandatory_num_hole_cards=2
    start_stack : int
        number of chips each player starts with
    low_end_straight : bool, optional
        toggle to include the low ace straight within valid hands, by
        default True
    order : Optional[List[str]], optional
        optional custom order of hand ranks, must be permutation of
        ['sf', 'fk', 'fh', 'fl', 'st', 'tk', 'tp', 'pa', 'hc']. if
        order=None, hands are ranked by rarity. by default None

    Examples
    --------

        >>> Dealer( # 1-2 Heads Up No Limit Texas Hold'em
        ...     num_players=2, num_streets=4, blinds=[1, 2], antes=0,
        ...     raise_sizes=float('inf'), num_raises=float('inf'),
        ...     num_suits=4, num_ranks=13, num_hole_cards=2,
        ...     mandatory_num_hole_cards=0, start_stack=200
        ... )
        >>> Dealer( # 1-2 6 Player PLO
        ...     num_players=6, num_streets=4, blinds=[0, 1, 2, 0, 0, 0],
        ...     antes=0, raise_sizes='pot', num_raises=float('inf'),
        ...     num_suits=4, num_ranks=13, num_hole_cards=4,
        ...     mandatory_num_hole_cards=2, start_stack=200
        ... )
        >>> Dealer( # 1-2 Heads Up No Limit Short Deck
        ...     num_players=2, num_streets=4, blinds=[1, 2], antes=0,
        ...     raise_sizes=float('inf'), num_raises=float('inf'),
        ...     num_suits=4, num_ranks=9, num_hole_cards=2,
        ...     mandatory_num_hole_cards=0, start_stack=200,
        ...     order=[
        ...         'sf', 'fk', 'fl', 'fh', 'st',
        ...         'tk', 'tp', 'pa', 'hc'
        ...         ]
        ... )
    """

    def __init__(
        self,
        num_players: int,
        num_streets: int,
        blinds: Union[int, List[int]],
        antes: Union[int, List[int]],
        raise_sizes: Union[
            int, Literal["pot", "inf"], List[Union[int, Literal["pot", "inf"]]]
        ],
        num_raises: Union[int, Literal["inf"], List[Union[int, Literal["inf"]]]],
        num_suits: int,
        num_ranks: int,
        num_hole_cards: int,
        num_community_cards: Union[int, List[int]],
        num_cards_for_hand: int,
        mandatory_num_hole_cards: int,
        start_stack: int,
        low_end_straight: bool = True,
        order: Optional[List[str]] = None,
    ) -> None:
        def check_inp(
            var: Union[List[Any], Any], expect_num: int, error_msg: str
        ) -> List[Any]:
            if isinstance(var, list):
                if len(var) != expect_num:
                    raise error.InvalidConfigError(error_msg)
                return var
            return [var] * expect_num

        error_msg = "incorrect {} distribution, expected list of length {}, got {}"
        blinds = check_inp(
            blinds, num_players, error_msg.format("blind", num_players, str(blinds)),
        )
        antes = check_inp(
            antes, num_players, error_msg.format("ante", num_players, str(antes))
        )
        raise_sizes = check_inp(
            raise_sizes,
            num_streets,
            error_msg.format("raise size", num_streets, str(raise_sizes)),
        )
        num_raises = check_inp(
            num_raises,
            num_streets,
            error_msg.format("number of raises", num_streets, str(num_raises)),
        )
        num_community_cards = check_inp(
            num_community_cards,
            num_streets,
            error_msg.format("community card", num_streets, str(num_community_cards)),
        )

        def clean_rs(
            raise_size: Union[int, Literal["pot", "inf"]]
        ) -> Union[float, Literal["pot"]]:
            if raise_size == "inf":
                return float(raise_size)
            if raise_size == "pot":
                return raise_size
            if isinstance(raise_size, int):
                return raise_size
            raise error.InvalidRaiseSizeError(
                f"unknown raise size, expected one of (int, 'inf', 'pot'),"
                f" got {raise_size}"
            )

        # config
        self.num_players = num_players
        self.num_streets = num_streets
        self.blinds = blinds
        self.antes = antes
        self.big_blind = blinds[1]
        self.raise_sizes = [clean_rs(raise_size) for raise_size in raise_sizes]
        self.num_raises = [float(raise_num) for raise_num in num_raises]
        self.num_suits = num_suits
        self.num_ranks = num_ranks
        self.num_hole_cards = num_hole_cards
        self.num_community_cards = num_community_cards
        self.num_cards_for_hand = num_cards_for_hand
        self.mandatory_num_hole_cards = mandatory_num_hole_cards
        self.start_stack = start_stack

        # dealer
        self.action = -1
        self.active = [False] * self.num_players
        self.button = 0
        self.community_cards: List[poker.Card] = []
        self.deck = poker.Deck(self.num_suits, self.num_ranks)
        self.evaluator = poker.Evaluator(
            self.num_suits,
            self.num_ranks,
            self.num_cards_for_hand,
            self.mandatory_num_hole_cards,
            low_end_straight=low_end_straight,
            order=order,
        )
        self.history: List[Tuple[int, int, bool]] = []
        self.hole_cards: List[List[poker.Card]] = []
        self.largest_raise = 0
        self.pot = 0
        self.pot_commits = [0] * self.num_players
        self.stacks = [self.start_stack] * self.num_players
        self.street = 0
        self.street_commits = [0] * self.num_players
        self.street_option = [False] * self.num_players
        self.street_raises = 0

        # render
        self.viewer: Optional[render.PokerViewer]
        self.viewer = None
        self.ascii_viewer = render.ASCIIViewer(
            num_players, num_hole_cards, sum(num_community_cards)
        )

    def __str__(self) -> str:
        config = self._render_config()
        return self.ascii_viewer._parse_string(config)

    def __repr__(self) -> str:
        string = (
            f"Dealer ({id(self)}) - num players: {self.num_players}, "
            f"num streets: {self.num_streets}"
        )
        return string

    def reset(
        self, reset_button: bool = False, reset_stacks: bool = False
    ) -> ObservationDict:
        """Resets the table. Shuffles the deck, deals new hole cards
        to all players, moves the button and collects blinds and antes.

        Parameters
        ----------
        reset_button : bool, optional
            reset button to first position at table, by default False
        reset_stacks : bool, optional
            reset stack sizes to starting stack size, by default False

        Returns
        -------
        ObservationDict
            observation dictionary

        Examples
        --------

        >>> dealer = Dealer(**configs.LEDUC_TWO_PLAYER)
        >>> dealer.reset()
        ... {'action': 1,
        ...  'active': [True, True],
        ...  'button': 1,
        ...  'call': 0,
        ...  'community_cards': [],
        ...  'hole_cards': [[Card (139879188163600): A♥], [Card (139879188163504): A♠]],
        ...  'max_raise': 2,
        ...  'min_raise': 2,
        ...  'pot': 2,
        ...  'stacks': [9, 9],
        ...  'street_commits': [0, 0]}
        """
        if reset_stacks:
            self.active = [True] * self.num_players
            self.stacks = [self.start_stack] * self.num_players
        else:
            self.active = [stack > 0 for stack in self.stacks]
            if sum(self.active) <= 1:
                raise error.TooFewActivePlayersError(
                    "not enough players have chips, set reset_stacks=True"
                )
        if reset_button:
            self.button = 0
        else:
            self.button = (self.button + 1) % self.num_players

        self.deck.shuffle()
        self.community_cards = self.deck.draw(self.num_community_cards[0])
        self.history = []
        self.hole_cards = [
            self.deck.draw(self.num_hole_cards) for _ in range(self.num_players)
        ]
        self.largest_raise = self.big_blind
        self.pot = 0
        self.pot_commits = [0] * self.num_players
        self.street = 0
        self.street_commits = [0] * self.num_players
        self.street_option = [False] * self.num_players
        self.street_raises = 0

        self.action = self.button
        # in heads up button posts small blind
        if self.num_players > 2:
            self._move_action()
        self._collect_multiple_bets(bets=self.antes, street_commits=False)
        self._collect_multiple_bets(bets=self.blinds, street_commits=True)
        self._move_action()
        self._move_action()

        return self._observation(False)

    def step(self, bet: float) -> Tuple[ObservationDict, List[int], List[bool]]:
        """Advances poker game to next player. If the bet is 0, it is
        either considered a check or fold, depending on the previous
        action. The given bet is always rounded to the closest valid bet
        size. When it is the same distance from two valid bet sizes
        the smaller bet size is used, e.g. if the min raise is 10 and
        the bet is 5, it is rounded down to 0.

        Parameters
        ----------
        bet : int
            number of chips bet by player currently active

        Returns
        -------
        Tuple[ObservationDict, List[int], List[bool]]
            observation dictionary, payouts for every player, boolean value for every
            player showing if that player is still active in the round

        Examples
        --------

        >>> dealer = Dealer(**configs.LEDUC_TWO_PLAYER)
        >>> obs = dealer.reset()
        >>> dealer.step(0)
        ... ({'action': 0,
        ...  'active': [True, True],
        ...  'button': 1,
        ...  'call': 0,
        ...  'community_cards': [],
        ...  'hole_cards': [[Card (139879188163600): A♥], [Card (139879188163504): A♠]],
        ...  'max_raise': 2,
        ...  'min_raise': 2,
        ...  'pot': 2,
        ...  'stacks': [9, 9],
        ...  'street_commits': [0, 0]},
        ...  [0, 0],
        ...  [False, False])
        """
        if self.action == -1:
            if any(self.active):
                done = self._done()
                payouts = self._payouts()
                observation = self._observation(all(done))
                return observation, payouts, done
            raise error.TableResetError("call reset() before calling first step()")

        fold = bet < 0
        bet = round(bet)

        call, min_raise, max_raise = self._bet_sizes()
        # round bet to nearest sizing
        bet = self._clean_bet(bet, call, min_raise, max_raise)

        # only fold if player cannot check
        if call and ((bet < call) or fold):
            self.active[self.action] = False
            bet = 0

        # if bet is full raise record as largest raise
        if bet and (bet - call) >= self.largest_raise:
            self.largest_raise = bet - call
            self.street_raises += 1

        self._collect_bet(bet)

        self.history.append((self.action, int(bet), bool(fold)))

        self.street_option[self.action] = True
        self._move_action()

        # if all agreed go to next street
        if self._all_agreed():
            self.action = self.button
            self._move_action()
            # if at most 1 player active and not all in turn up all
            # community cards and evaluate hand
            while True:
                self.street += 1
                full_streets = self.street >= self.num_streets
                all_in = [
                    bool(active * (stack == 0))
                    for active, stack in zip(self.active, self.stacks)
                ]
                all_all_in = sum(self.active) - sum(all_in) <= 1
                if full_streets:
                    break
                self.community_cards += self.deck.draw(
                    self.num_community_cards[self.street]
                )
                if not all_all_in:
                    break
            self.street_commits = [0] * self.num_players
            self.street_option = [not active for active in self.active]
            self.street_raises = 0

        done = self._done()
        payouts = self._payouts()
        if all(done):
            self.action = -1
            self.pot = 0
            self.stacks = [
                stack + payout + pot_commit
                for stack, payout, pot_commit in zip(
                    self.stacks, payouts, self.pot_commits
                )
            ]
        observation = self._observation(all(done))
        return observation, payouts, done

    def _render_config(self) -> render.viewer.RenderConfig:
        action = int(self.action)
        active = self.active
        all_in = [
            bool(active * (stack == 0))
            for active, stack in zip(self.active, self.stacks)
        ]
        community_cards = self.community_cards
        button = int(self.button)
        done = all(self._done())
        hole_cards = self.hole_cards
        pot = int(self.pot)
        payouts = self._payouts()
        street_commits = self.street_commits
        stacks = self.stacks

        config: render.viewer.RenderConfig = {
            "action": action,
            "active": active,
            "all_in": all_in,
            "community_cards": community_cards,
            "button": button,
            "done": done,
            "hole_cards": hole_cards,
            "pot": pot,
            "payouts": payouts,
            "prev_action": None if not self.history else self.history[-1],
            "street_commits": street_commits,
            "stacks": stacks,
        }

        return config

    def render(self, mode: str = "human", sleep: float = 0, **kwargs: Any) -> None:
        """Renders poker table. Render mode options are: ascii, human

        Parameters
        ----------
        mode : str, optional
            toggle for using different renderer, by default 'human'
        sleep : float, optional
            time to wait after rendering, by default 0
        """
        viewer: Optional[Type[render.PokerViewer]] = None
        render_modes = ["ascii", "human"]
        if self.viewer is None:
            if mode == "ascii":
                viewer = render.ASCIIViewer
            elif mode == "human":
                viewer = render.GraphicViewer
            else:
                raise error.InvalidRenderModeError(
                    (f"incorrect render mode {mode}," f"use one of {render_modes}")
                )
            self.viewer = viewer(
                self.num_players,
                self.num_hole_cards,
                sum(self.num_community_cards),
                **kwargs,
            )

        config = self._render_config()

        self.viewer.render(config, sleep)

    def win_probabilities(self, verbose: bool = False) -> List[float]:
        """Computes win probabilities for each player by exhaustively checking every
        possible combination of remaining community cards.

        Parameters
        ----------
        verbose : bool, optional
            toggle to print progress of computing win probabilities, default False

        Returns
        -------
        List[float]
            win probabilities
        """
        hand_strengths = []
        num_additional_comm_cards = sum(self.num_community_cards) - len(
            self.community_cards
        )
        num_comm_combinations = poker.evaluator._ncr(
            len(self.deck.cards), num_additional_comm_cards
        )
        comm_combinations = itertools.combinations(
            self.deck.cards, num_additional_comm_cards
        )
        hands_won = {player_idx: 0 for player_idx in range(self.num_players)}
        for additional_comm_cards in comm_combinations:
            community_cards = self.community_cards + list(additional_comm_cards)
            hand_strengths = self._eval_hands(self.hole_cards, community_cards)
            best_hand = min(hand_strengths)
            for player_idx, hand_strength in enumerate(hand_strengths):
                if hand_strength == best_hand:
                    hands_won[player_idx] += 1
        win_probs = [
            hands_won[player_idx] / num_comm_combinations
            for player_idx in range(self.num_players)
        ]
        return win_probs

    def _all_agreed(self) -> bool:
        # not all agreed if not all players had chance to act
        if not all(self.street_option):
            return False
        # all agreed if street commits equal to maximum street commit
        street_commit = [
            street_commit == max(self.street_commits)
            for street_commit in self.street_commits
        ]
        # or player is all in
        all_in = [stack == 0 for stack in self.stacks]
        # or player is not active
        active = [not active for active in self.active]
        agreed = [
            _street_commit or _all_in or _active
            for _street_commit, _all_in, _active in zip(street_commit, all_in, active)
        ]
        return all(agreed)

    def _bet_sizes(self) -> Tuple[int, int, int]:
        # call difference between commit and maximum commit
        call = max(self.street_commits) - self.street_commits[self.action]
        # min raise at least largest previous raise
        # if limit game min and max raise equal to raise size
        raise_size = self.raise_sizes[self.street]
        if isinstance(raise_size, int):
            max_raise = min_raise = raise_size + call
        else:
            min_raise = max(self.big_blind, self.largest_raise + call)
            if raise_size == "pot":
                max_raise = self.pot + call * 2
            elif raise_size == float("inf"):
                max_raise = self.stacks[self.action]
        # if maximum number of raises in street
        # was reached cap raise at 0
        if self.street_raises >= self.num_raises[self.street]:
            min_raise = max_raise = 0
        # if last full raise was done by active player
        # (another player has raised less than minimum raise amount)
        # cap active players raise size to 0
        if self.street_raises and call < self.largest_raise:
            min_raise = max_raise = 0
        # clip bets to stack size
        call = min(call, self.stacks[self.action])
        min_raise = min(min_raise, self.stacks[self.action])
        max_raise = min(max_raise, self.stacks[self.action])
        return call, min_raise, max_raise

    @staticmethod
    def _clean_bet(bet: int, call: int, min_raise: int, max_raise: int) -> int:
        # find closest bet size to actual bet
        # round down for tie, order is fold/check -> call -> raise
        bet = max(0, bet)
        idx = argmin([abs(value - bet) for value in [0, call, min_raise, max_raise]])
        # if call closest
        if idx == 1:
            return call
        # if min raise or max raise closest
        if idx in (2, 3):
            return round(min(max_raise, max(min_raise, bet)))
        # if check/fold closest
        return 0

    def _collect_multiple_bets(
        self, bets: List[int], street_commits: bool = True
    ) -> None:
        # roll list to action
        bets = bets[-self.action :] + bets[: -self.action]
        bets = [
            (stack > 0) * active * bet
            for stack, active, bet in zip(self.stacks, self.active, bets)
        ]
        if street_commits:
            self.street_commits = [
                street_commit + bet
                for street_commit, bet in zip(self.street_commits, bets)
            ]
        self.pot += sum(bets)
        self.pot_commits = [
            pot_commit + bet for pot_commit, bet in zip(self.pot_commits, bets)
        ]
        self.stacks = [stack - bet for stack, bet in zip(self.stacks, bets)]

    def _collect_bet(self, bet: int) -> None:
        # bet only as large as stack size
        bet = min(self.stacks[self.action], bet)

        self.pot += bet
        self.pot_commits[self.action] += bet
        self.street_commits[self.action] += bet
        self.stacks[self.action] -= bet

    def _done(self) -> List[bool]:
        if self.street >= self.num_streets or sum(self.active) <= 1:
            # end game
            return [True] * self.num_players
        done = [
            not active or stack == 0 for active, stack in zip(self.active, self.stacks)
        ]
        return done

    def _observation(self, done: bool) -> ObservationDict:
        if done:
            call = min_raise = max_raise = 0
        else:
            call, min_raise, max_raise = self._bet_sizes()
        observation: ObservationDict = {
            "action": self.action,
            "active": self.active,
            "button": self.button,
            "call": call,
            "community_cards": self.community_cards,
            "hole_cards": self.hole_cards[self.action],
            "max_raise": max_raise,
            "min_raise": min_raise,
            "pot": self.pot,
            "stacks": self.stacks,
            "street_commits": self.street_commits,
        }
        return observation

    def _payouts(self) -> List[int]:
        # players that have folded lose their bets
        payouts = [
            -1 * pot_commit * (not active)
            for pot_commit, active in zip(self.pot_commits, self.active)
        ]
        # if only one player left give that player all chips
        if sum(self.active) == 1:
            payouts = [
                payout + active * (self.pot - pot_commit)
                for payout, active, pot_commit in zip(
                    payouts, self.active, self.pot_commits
                )
            ]
            return payouts
        # if last street played and still multiple players active
        elif self.street >= self.num_streets:
            payouts = self._eval_round()
            payouts = [
                payout - pot_commit
                for payout, pot_commit in zip(payouts, self.pot_commits)
            ]
            return payouts
        return payouts

    def _eval_hands(
        self, hole_cards: List[List[poker.Card]], community_cards: List[poker.Card]
    ) -> List[int]:
        # grab array of hand strength and pot commits
        worst_hand = self.evaluator.table.max_rank + 1
        hand_strengths = []
        for player in range(self.num_players):
            # if not active hand strength set
            # to 1 worse than worst possible rank
            hand_strength = (
                self.evaluator.evaluate(hole_cards[player], community_cards)
                if self.active[player]
                else worst_hand
            )
            hand_strengths.append(hand_strength)
        return hand_strengths

    def _eval_round(self) -> List[int]:
        # grab array of hand strength and pot commits
        hand_strengths = self._eval_hands(self.hole_cards, self.community_cards)
        hands: List[List[int]] = [
            [player_idx, hand_strength, self.pot_commits[player_idx]]
            for player_idx, hand_strength in enumerate(hand_strengths)
        ]
        # sort hands by hand strength and pot commits
        hands = sorted(hands, key=operator.itemgetter(1, 2))
        pot = self.pot
        remainder = 0
        payouts = [0] * self.num_players
        worst_hand = self.evaluator.table.max_rank + 1
        # iterate over hand strength and
        # pot commits from smallest to largest
        for hand_idx, (_, strength, pot_commit) in enumerate(hands):
            eligible = [
                player_idx
                for player_idx, other_strength, _ in hands
                if other_strength == strength
            ]
            # cut can only be as large as lowest player commit amount
            cut = [min(hand[2], pot_commit) for hand in hands]
            split_pot = sum(cut)
            if not split_pot:
                continue
            split = split_pot // len(eligible)
            remain = split_pot % len(eligible)
            for player_idx in eligible:
                payouts[player_idx] += split
            remainder += remain
            # remove chips from players and pot
            for idx in range(len(cut)):
                hands[idx][2] -= cut[idx]
            pot -= split_pot
            # remove player from next split pot
            hands[hand_idx][1] = worst_hand
            if pot == 0:
                break
        # give worst position player remainder chips
        if remainder:
            # worst player is first player after button involved in pot
            for player_idx in range(1, self.num_players + 1):
                if payouts[player_idx + self.button % self.num_players]:
                    payouts[player_idx] += remainder
                    break
        return payouts

    def _move_action(self) -> "Dealer":
        action = self.action
        for idx in range(1, self.num_players + 1):
            action = (self.action + idx) % self.num_players
            if self.active[action]:
                break
            else:
                self.street_option[action] = True
        self.action = action
        return self


def argmin(values: List[int]) -> int:
    minimum = float("inf")
    minimum_idx = 0
    for idx, value in enumerate(values):
        if value < minimum:
            minimum_idx = idx
            minimum = value
    return minimum_idx
