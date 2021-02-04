import time

from clubs import render


def test_base():
    viewer = render.PokerViewer(0, 0, 0)
    start = time.time()
    viewer.render({}, sleep=5)
    assert time.time() - start > 1
