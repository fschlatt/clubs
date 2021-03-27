from typing import Any, Dict


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
        self, num_players: int, num_hole_cards: int, num_community_cards: int, **kwargs,
    ) -> None:
        self.num_players = num_players
        self.num_hole_cards = num_hole_cards
        self.num_community_cards = num_community_cards

    def render(self, config: Dict[str, Any], sleep: float = 0) -> None:
        """Render the table based on the table configuration

        Parameters
        ----------
        config : Dict[str, Any]
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
        ...     'dealer': 0, # int - position of dealer
        ...     'done': False, # bool - toggle if hand is completed
        ...     'hole_cards': [[Card("Ah")], [Card("Ac")]], # List[List[Card]] -
        ...                                                 # list of list of hole card
        ...     'pot': 10, # int - chips in pot
        ...     'payouts': [0, 0], # List[int] - list of chips won for each player
        ...     'prev_action': [1, 10, 0], # Tuple[int, int, int] -
        ...                                # last position bet and fold
        ...     'street_commits': [10, 20] # List[int] - list of number of
        ...                                # chips added to pot from each
        ...                                # player on current street
        ...     'stacks': [100, 100] # List[int] - list of stack sizes
        ... }
        """
        raise NotImplementedError()
