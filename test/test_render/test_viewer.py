import time

from clubs import render


def test_base():
    viewer = render.PokerViewer(0, 0, 0)
    start = time.time()
    viewer.render({}, sleep=1)
    assert time.time() - start > 1
