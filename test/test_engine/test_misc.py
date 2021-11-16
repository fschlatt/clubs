import random

import pytest

import clubs
from clubs import error


def test_game() -> None:

    config = clubs.configs.LEDUC_TWO_PLAYER

    dealer = clubs.poker.Dealer(**config)

    dealer.deck = dealer.deck.trick(
        [clubs.Card("Qs"), clubs.Card("Ks"), clubs.Card("Qh")]
    )

    obs = dealer.reset(reset_button=True, reset_stacks=True)

    bet = 2
    _ = dealer.step(bet)
    bet = 4
    _ = dealer.step(bet)
    bet = 2
    _ = dealer.step(bet)
    bet = 0
    _ = dealer.step(bet)
    bet = 2
    _ = dealer.step(bet)
    bet = 2
    obs, payout, done = dealer.step(bet)

    assert all(done)
    assert payout[0] > payout[1]
    assert payout[0] == 7


def test_heads_up() -> None:

    config = clubs.configs.NO_LIMIT_HOLDEM_TWO_PLAYER

    dealer = clubs.poker.Dealer(**config)

    obs = dealer.reset(reset_button=True, reset_stacks=True)

    assert obs["action"] == 0
    assert obs["call"] == 1
    assert obs["min_raise"] == 3
    assert obs["max_raise"] == 199

    bet = 1
    obs, *_ = dealer.step(bet)

    assert obs["call"] == 0
    assert obs["min_raise"] == 2
    assert obs["max_raise"] == 198


def test_reset() -> None:
    config = clubs.configs.NO_LIMIT_HOLDEM_SIX_PLAYER

    dealer = clubs.poker.Dealer(**config)

    obs = dealer.reset(reset_button=True, reset_stacks=True)
    assert obs["action"] == 3

    for idx in range(6):
        while True:
            *_, done = dealer.step(0)
            if all(done):
                break

        obs = dealer.reset()
        assert obs["action"] == (4 + idx) % 6


def test_init() -> None:

    config = clubs.configs.NO_LIMIT_HOLDEM_TWO_PLAYER.copy()

    blinds = config["blinds"]
    antes = config["antes"]
    raise_sizes = config["raise_sizes"]
    num_raises = config["num_raises"]
    num_community_cards = config["num_community_cards"]

    config["blinds"] = [0]
    with pytest.raises(error.InvalidConfigError):
        clubs.poker.Dealer(**config)
    config["blinds"] = blinds

    config["antes"] = [0]
    with pytest.raises(error.InvalidConfigError):
        clubs.poker.Dealer(**config)
    config["antes"] = antes

    config["raise_sizes"] = [0]
    with pytest.raises(error.InvalidConfigError):
        clubs.poker.Dealer(**config)
    config["raise_sizes"] = raise_sizes

    config["num_raises"] = [0]
    with pytest.raises(error.InvalidConfigError):
        clubs.poker.Dealer(**config)
    config["num_raises"] = num_raises

    config["num_community_cards"] = [0]
    with pytest.raises(error.InvalidConfigError):
        clubs.poker.Dealer(**config)
    config["num_community_cards"] = num_community_cards

    config["blinds"] = 0
    config["antes"] = 0
    config["raise_sizes"] = 0
    config["num_raises"] = 0
    config["num_community_cards"] = 0

    dealer = clubs.poker.Dealer(**config)

    assert list(dealer.blinds) == [0, 0]
    assert list(dealer.antes) == [0, 0]
    assert list(dealer.raise_sizes) == [0, 0, 0, 0]
    assert list(dealer.num_raises) == [0, 0, 0, 0]
    assert list(dealer.num_community_cards) == [0, 0, 0, 0]

    config["blinds"] = blinds
    config["antes"] = antes
    config["raise_sizes"] = raise_sizes
    config["num_raises"] = num_raises
    config["num_community_cards"] = num_community_cards

    config["raise_sizes"] = "lala"  # type: ignore
    with pytest.raises(error.InvalidRaiseSizeError):
        clubs.poker.Dealer(**config)
    config["raise_sizes"] = raise_sizes


def test_str_repr() -> None:

    config = clubs.configs.NO_LIMIT_HOLDEM_TWO_PLAYER

    dealer = clubs.poker.Dealer(**config)

    assert len(str(dealer)) == 1242
    string = (
        f"Dealer ({id(dealer)}) - num players: {dealer.num_players}, "
        f"num streets: {dealer.num_streets}"
    )
    assert repr(dealer) == string


def test_init_step() -> None:

    config = clubs.configs.NO_LIMIT_HOLDEM_TWO_PLAYER

    dealer = clubs.poker.Dealer(**config)

    with pytest.raises(error.TableResetError):
        dealer.step(0)


def test_win_probabilities() -> None:

    random.seed(1)

    config = clubs.configs.NO_LIMIT_HOLDEM_NINE_PLAYER
    dealer = clubs.poker.Dealer(**config)
    dealer.reset()

    dealer.step(-1)
    dealer.step(2)
    dealer.step(2)
    dealer.step(2)
    dealer.step(-1)
    dealer.step(2)
    dealer.step(2)
    dealer.step(1)
    dealer.step(0)
    win_probs = dealer.win_probabilities()
    assert pytest.approx(sum(win_probs), 1)
    assert all(
        win_prob != 0 or not active
        for win_prob, active in zip(win_probs, dealer.active)
    )
