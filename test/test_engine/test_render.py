import http.client
import io
import re
import time
import urllib.error
import urllib.request
from contextlib import redirect_stdout
from typing import Optional
from xml.etree import ElementTree as et

import pytest

import clubs
from clubs import error, poker, render


@pytest.fixture
def dealer() -> clubs.Dealer:
    config = clubs.configs.NO_LIMIT_HOLDEM_SIX_PLAYER

    dealer = clubs.Dealer(**config)

    def _render_config() -> render.viewer.RenderConfig:
        return {
            "action": 0,
            "active": [True, True],
            "all_in": [False, False],
            "community_cards": [],
            "button": 0,
            "done": False,
            "hole_cards": [[poker.Card("Ah"), poker.Card("Ad")], []],
            "pot": 10,
            "payouts": [0, 0],
            "prev_action": (1, 10, False),
            "street_commits": [10, 20],
            "stacks": [200, 200],
        }

    dealer._render_config = _render_config  # type: ignore

    return dealer


def test_error(dealer: clubs.Dealer) -> None:
    with pytest.raises(error.InvalidRenderModeError):
        dealer.render("lala")


def test_ascii(dealer: clubs.Dealer) -> None:
    dealer.viewer = None
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        dealer.render("ascii")
    string = stdout.getvalue()

    action_string = "Action on Player 1"
    sub_strings = [
        f"A{chr(9829)},A{chr(9830)} 200",
        "??",
        action_string,
    ]
    assert all(sub_string in string for sub_string in sub_strings)


def test_human(dealer: clubs.Dealer) -> None:
    dealer.render()

    assert isinstance(dealer.viewer, render.GraphicViewer)
    port = dealer.viewer.port

    start = time.time()
    response: Optional[http.client.HTTPResponse] = None
    while True:
        if time.time() - start > 10:
            break
        try:
            response = urllib.request.urlopen(f"http://localhost:{port}")
            break
        except urllib.error.URLError:
            pass
        time.sleep(1)

    assert isinstance(response, http.client.HTTPResponse) and response.status == 200
    content = response.read().decode().replace("\n", "")
    match = re.search(r"<\?xml.*?><svg.*</svg>", content)
    assert match is not None
    svg_xml_string = match.group(0)

    xml = et.fromstring(svg_xml_string)
    assert len(xml.findall(".//svg[@class='player']")) == 6
