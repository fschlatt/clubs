from typing import Any, List, Optional, Tuple, TypedDict

from .. import poker


class RenderConfig(TypedDict):
    action: int
    active: List[bool]
    all_in: List[bool]
    community_cards: List[poker.Card]
    button: int
    done: bool
    hole_cards: List[List[poker.Card]]
    pot: int
    payouts: List[int]
    prev_action: Optional[Tuple[int, int, bool]]
    street_commits: List[int]
    stacks: List[int]


class PokerViewer:
    """Base class for renderer. Any renderer must subclass this renderer
    and implement the function render

    Parameters
    ----------
    num_players : int
        number of player
    num_hole_cards : int
        number of hole cards
    num_community_cards : int
        number of community cards
    """

    def __init__(
        self,
        num_players: int,
        num_hole_cards: int,
        num_community_cards: int,
        **kwargs: Any,
    ) -> None:
        self.num_players = num_players
        self.num_hole_cards = num_hole_cards
        self.num_community_cards = num_community_cards

    def render(self, config: RenderConfig, sleep: float = 0) -> None:
        """Render the table based on the table configuration

        Parameters
        ----------
        config : RenderConfig
            game configuration dictionary

        sleep : float, optional
            sleep time after render, by default 0

        Examples
        --------
        >>> from clubs import Card
        >>> config = {
        ...     'action': 0, # int - position of active player
        ...     'active': [True, True], # List[bool] - list of active players
        ...     'all_in': [False, False], # List[bool] - list of all in players
        ...     'community_cards': [], # List[Card] - list of community cards
        ...     'button': 0, # int - position of dealer button
        ...     'done': False, # bool - toggle if hand is completed
        ...     'hole_cards': [[Card("Ah")], [Card("Ac")]], # List[List[Card]] -
        ...                                                 # list of list of hole card
        ...     'pot': 10, # int - chips in pot
        ...     'payouts': [0, 0], # List[int] - list of chips won for each player
        ...     'prev_action': (1, 10, False], # Tuple[int, int, int] -
        ...                                    # last position bet and fold
        ...     'street_commits': [10, 20], # List[int] - list of number of
        ...                                 # chips added to pot from each
        ...                                 # player on current street
        ...     'stacks': [100, 100] # List[int] - list of stack sizes
        ... }
        """
        raise NotImplementedError()
