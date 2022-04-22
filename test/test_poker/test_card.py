import random

import pytest

from clubs import error, poker


def test_draw() -> None:

    deck = poker.Deck(2, 3)

    cards = deck.draw(1)
    assert len(cards) == 1

    cards = deck.draw(3)
    assert len(cards) == 3

    cards = deck.draw(4)
    assert len(cards) == 2

    cards = deck.draw(1)
    assert len(cards) == 0


def test_trick() -> None:
    random.seed(42)

    deck = poker.Deck(4, 13).trick([poker.Card("Ah"), poker.Card("2s")])
    deck.shuffle()

    cards = deck.draw(2)
    assert cards[0] == poker.Card("Ah")
    assert cards[1] == poker.Card("2s")

    deck = deck.shuffle()
    cards = deck.draw(2)
    assert cards[0] == poker.Card("Ah")
    assert cards[1] == poker.Card("2s")

    deck = deck.untrick().shuffle()
    cards = deck.draw(2)
    assert cards[0] != poker.Card("Ah")
    assert cards[1] != poker.Card("2s")


def test_invalid_init() -> None:
    with pytest.raises(error.InvalidRankError):
        poker.Card("1s")
    with pytest.raises(error.InvalidRankError):
        poker.Card("1t")
    with pytest.raises(error.InvalidRankError):
        poker.Deck(0, 0)
    with pytest.raises(error.InvalidRankError):
        poker.Deck(2, 14)

    with pytest.raises(error.InvalidSuitError):
        poker.Card("At")
    with pytest.raises(error.InvalidSuitError):
        poker.Deck(0, 1)
    with pytest.raises(error.InvalidSuitError):
        poker.Deck(5, 1)


def test_ops() -> None:
    card = poker.Card("Ac")

    assert card & card
    assert card & card._int
    assert card | card
    assert card | card._int
    assert card << 0 == card._int
    assert card._int << 0 == card._int
    assert card >> 0 == card._int
    assert card._int >> 0 == card._int

    with pytest.raises(NotImplementedError):
        assert card == 0


def test_deck_str_repr() -> None:
    deck = poker.Deck(4, 13)
    assert repr(deck) == f"Deck ({id(deck)}): {str(deck)}"

    deck = poker.Deck(4, 13, unicode=True)
    assert repr(deck) == f"Deck ({id(deck)}): {str(deck)}"


def test_card_str_repr() -> None:
    card = poker.Card("Ac")
    assert repr(card) == f"Card ({id(card)}): {card}"

    deck = poker.Deck(4, 13, unicode=True)

    full_deck = [
        '🂢', '🂲', '🃂', '🃒', '🂣', '🂳', '🃃', '🃓', '🂤', '🂴', '🃄', '🃔', '🂥', '🂵', '🃅', '🃕',
        '🂦', '🂶', '🃆', '🃖', '🂧', '🂷', '🃇', '🃗', '🂨', '🂸', '🃈', '🃘', '🂩', '🂹', '🃉', '🃙',
        '🂪', '🂺', '🃊', '🃚', '🂫', '🂻', '🃋', '🃛', '🂭', '🂽', '🃍', '🃝', '🂮', '🂾', '🃎', '🃞',
        '🂡', '🂱', '🃁', '🃑'
    ]

    assert [str(c) for c in deck.full_deck] == full_deck
