import http.client
import time
import urllib.error
import urllib.request
from typing import Optional

import pytest

from clubs.render import graphic


def test_init() -> None:
    viewer = graphic.GraphicViewer(2, 2, 5)
    assert viewer.svg_poker.base_svg.name == "base"


def test_svg() -> None:
    with pytest.raises(FileNotFoundError):
        graphic._SVGElement("foo")

    table = graphic._SVGElement("table")
    assert 'class="table"' in str(table)
    assert "SVGElement<name=table" in repr(table)

    patterns = graphic._SVGElement("patterns")
    assert isinstance(patterns.get_sub_svg("pattern"), graphic._SVGElement)
    sub_patterns = patterns.get_sub_svgs("pattern")
    assert len(sub_patterns) == 7
    with pytest.raises(KeyError):
        patterns.get_sub_svg("foo")
    with pytest.raises(KeyError):
        patterns.get_sub_svgs("foo")
    assert patterns.x == 0
    assert patterns.y == 0
    assert patterns.height == 0
    assert patterns.width == 0
    assert patterns.id is None
    assert patterns.view_box is None
    assert patterns.view_box_x is None
    assert patterns.view_box_y is None
    assert patterns.view_box_height is None
    assert patterns.view_box_width is None

    base = graphic._SVGElement("base")
    assert base.view_box == "0 0 1000 1000"
    assert base.view_box_x == 0
    assert base.view_box_y == 0
    assert base.view_box_height == 1000
    assert base.view_box_width == 1000

    base.view_box_x = 1
    base.view_box_y = 1
    base.view_box_height = 1
    base.view_box_width = 1
    assert base.view_box_x == 1
    assert base.view_box_y == 1
    assert base.view_box_height == 1
    assert base.view_box_width == 1

    base.view_box = "2 2 2 2"
    assert base.view_box == "2 2 2 2"


def test_rectangle() -> None:
    rectangle = graphic._RoundedRectangle(0, 0, 100, 100)

    x, y = rectangle.edge(0)
    assert pytest.approx(x, 0)
    assert pytest.approx(y, -50)
    x, y = rectangle.edge(0.25)
    assert pytest.approx(x, -50)
    assert pytest.approx(y, 0)
    x, y = rectangle.edge(0.5)
    assert pytest.approx(x, 0)
    assert pytest.approx(y, 50)
    x, y = rectangle.edge(0.75)
    assert pytest.approx(x, 50)
    assert pytest.approx(y, 0)


def test_port() -> None:
    port = 6789
    viewer = graphic.GraphicViewer(20, 2, 5, port=port)
    assert viewer.port == port

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

    assert response and response.status == 200
