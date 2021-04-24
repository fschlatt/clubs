import pytest

from clubs import poker, render


def test_base() -> None:
    config: render.viewer.RenderConfig = {
        "action": 0,
        "active": [True, True],
        "all_in": [False, False],
        "community_cards": [],
        "button": 0,
        "done": False,
        "hole_cards": [[poker.Card("Ah")], [poker.Card("Ac")]],
        "pot": 10,
        "payouts": [0, 0],
        "prev_action": (1, 10, False),
        "street_commits": [10, 20],
        "stacks": [100, 100],
    }
    viewer = render.PokerViewer(0, 0, 0)
    with pytest.raises(NotImplementedError):
        viewer.render(config, sleep=5)
