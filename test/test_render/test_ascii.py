import io
from contextlib import redirect_stdout

from clubs import poker, render


def test_init() -> None:
    viewer = render.ASCIIViewer(2, 2, 5)
    assert len(viewer.table) == 1061


def test_render() -> None:

    viewer = render.ASCIIViewer(2, 2, 5)

    config: render.viewer.RenderConfig = {
        "action": 0,
        "active": [True, True],
        "all_in": [False, False],
        "community_cards": [],
        "button": 0,
        "done": False,
        "hole_cards": [
            [poker.Card("Ah"), poker.Card("Ad")],
            [poker.Card("Kh"), poker.Card("Kd")],
        ],
        "pot": 10,
        "payouts": [0, 0],
        "prev_action": (1, 10, False),
        "street_commits": [10, 20],
        "stacks": [100, 100],
    }

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        viewer.render(config)
    string = stdout.getvalue()

    sub_strings = [f"A{chr(9829)}", f"A{chr(9830)}", "??", "20"]
    not_sub_strings = [f"K{chr(9829)}", f"K{chr(9830)}"]
    assert all(sub_string in string for sub_string in sub_strings)
    assert all(sub_string not in string for sub_string in not_sub_strings)

    config["active"] = [True, False]

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        viewer.render(config)
    string = stdout.getvalue()

    sub_strings = [f"A{chr(9829)}", f"A{chr(9830)}", "20"]
    not_sub_strings = ["??"]
    assert all(sub_string in string for sub_string in sub_strings)
    assert all(sub_string not in string for sub_string in not_sub_strings)

    config["active"] = [True, True]
    config["all_in"] = [False, True]

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        viewer.render(config)
    string = stdout.getvalue()

    sub_strings = [f"A{chr(9829)}", f"A{chr(9830)}", "20", "A"]
    not_sub_strings = [f"K{chr(9829)}", f"K{chr(9830)}"]
    assert all(sub_string in string for sub_string in sub_strings)
    assert all(sub_string not in string for sub_string in not_sub_strings)

    config["all_in"] = [False, False]
    config["prev_action"] = (1, 200, False)

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        viewer.render(config)
    string = stdout.getvalue()

    action_string = "Player 2 bet 200 Action on Player 1"
    sub_strings = [f"A{chr(9829)}", f"A{chr(9830)}", "20", action_string]
    not_sub_strings = [f"K{chr(9829)}", f"K{chr(9830)}"]
    assert all(sub_string in string for sub_string in sub_strings)
    assert all(sub_string not in string for sub_string in not_sub_strings)

    config["prev_action"] = (1, 0, True)

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        viewer.render(config)
    string = stdout.getvalue()

    action_string = "Player 2 folded Action on Player 1"
    sub_strings = [f"A{chr(9829)}", f"A{chr(9830)}", "20", action_string]
    not_sub_strings = [f"K{chr(9829)}", f"K{chr(9830)}"]
    assert all(sub_string in string for sub_string in sub_strings)
    assert all(sub_string not in string for sub_string in not_sub_strings)

    config["prev_action"] = (1, 0, False)

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        viewer.render(config)
    string = stdout.getvalue()

    action_string = "Player 2 checked Action on Player 1"
    sub_strings = [f"A{chr(9829)}", f"A{chr(9830)}", "20", action_string]
    not_sub_strings = [f"K{chr(9829)}", f"K{chr(9830)}"]
    assert all(sub_string in string for sub_string in sub_strings)
    assert all(sub_string not in string for sub_string in not_sub_strings)

    config["prev_action"] = None
    config["payouts"] = [2, 2]
    config["done"] = True

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        viewer.render(config)
    string = stdout.getvalue()

    action_string = "Players 1, 2 won 2, 2 respectively"
    sub_strings = [
        f"A{chr(9829)}",
        f"A{chr(9830)}",
        f"K{chr(9829)}",
        f"K{chr(9830)}",
        action_string,
    ]
    not_sub_strings = []
    assert all(sub_string in string for sub_string in sub_strings)
    assert all(sub_string not in string for sub_string in not_sub_strings)

    config["payouts"] = [10, 0]
    config["done"] = True

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        viewer.render(config)
    string = stdout.getvalue()

    action_string = "Player 1 won 10"
    sub_strings = [
        f"A{chr(9829)}",
        f"A{chr(9830)}",
        f"K{chr(9829)}",
        f"K{chr(9830)}",
        action_string,
    ]
    not_sub_strings = []
    assert all(sub_string in string for sub_string in sub_strings)
    assert all(sub_string not in string for sub_string in not_sub_strings)
