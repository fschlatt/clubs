import clubs


def main():
    avg_time = clubs.poker.evaluator.speed_test(4, 13, 5)
    print(f"Average time per evaluation: {avg_time}")
    print(f"Evaluations per second = {1.0/avg_time}")


if __name__ == "__main__":
    main()
