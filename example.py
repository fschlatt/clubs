import random
import time

import clubs


def main():
    # 1-2 no limit 6 player texas hold'em
    config = clubs.configs.NO_LIMIT_HOLDEM_NINE_PLAYER
    dealer = clubs.poker.Dealer(**config)
    obs = dealer.reset()

    dealer.render()
    time.sleep(1)

    while True:
        # number of chips a player must bet to call
        call = obs["call"]
        # smallest number of chips a player is allowed to bet for a raise
        min_raise = obs["min_raise"]

        rand = random.random()
        # 15% chance to fold
        if rand < 0.15:
            bet = 0
        # 80% chance to call
        elif rand < 0.95:
            bet = call
        # 5% to raise to min_raise
        else:
            bet = min_raise

        obs, rewards, done = dealer.step(bet)

        dealer.render()
        time.sleep(1)

        if all(done):
            break

    print(rewards)


if __name__ == "__main__":
    main()
