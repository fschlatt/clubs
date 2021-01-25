import http.client
import io
import re
import time
import urllib.error
import urllib.request
from contextlib import redirect_stdout
from typing import Optional
from xml.etree import ElementTree as et

import numpy as np
import pytest

import clubs
from clubs import error, render


@pytest.fixture
def dealer():
    config = clubs.configs.NO_LIMIT_HOLDEM_SIX_PLAYER

    dealer_ = clubs.poker.Dealer(**config)

    dealer_._render_config = lambda: {
        "action": 0,
        "active": np.array([1, 1]),
        "all_in": np.array([0, 0]),
        "community_cards": [clubs.Card("Ac")],
        "button": 0,
        "done": 0.0,
        "hole_cards": [
            [clubs.Card("Ah"), clubs.Card("Ad")],
            [clubs.Card("Ks"), clubs.Card("Kd")],
        ],
        "pot": 20,
        "payouts": np.array([0, 0]),
        "prev_action": None,
        "street_commits": np.array([0, 0]),
        "stacks": np.array([200, 200]),
    }
    return dealer_


def test_error(dealer: clubs.Dealer):
    with pytest.raises(error.InvalidRenderModeError):
        dealer.render("lala")


def test_ascii(dealer: clubs.Dealer):
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


def test_human(dealer: clubs.Dealer):
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


def test_asciimatics(dealer: clubs.Dealer):
    dealer.viewer = None
    dealer.render("asciimatics")
