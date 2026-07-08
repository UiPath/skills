import statistics


def summarize(numbers):
    """Return mean and stdev of a list of numbers; standard library only."""
    return {
        "mean": statistics.mean(numbers),
        "stdev": statistics.pstdev(numbers),
    }


print(summarize([10, 20, 30, 40]))
