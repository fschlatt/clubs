import clubs


def main():
    evaluator = clubs.poker.Evaluator(4, 13, 5)
    avg_time = evaluator.speed_test()
    print(f"Average time per evaluation: {avg_time}")
    print(f"Evaluations per second = {1.0/avg_time}")


if __name__ == "__main__":
    main()
