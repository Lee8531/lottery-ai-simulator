from collections import Counter
from typing import Sequence, Tuple

from lottery_sim.models import Draw5D, Pick5D


class Hot5DStrategy:
    name = "五位热号策略"

    def __init__(self, window: int = 30):
        self.window = window

    def generate(self, history: Sequence[Draw5D]) -> Pick5D:
        recent = _recent(history, self.window)
        if not recent:
            return (0, 0, 0, 0, 0)
        return tuple(_hot_digit(recent, position) for position in range(5))  # type: ignore[return-value]


class Cold5DStrategy:
    name = "五位冷号策略"

    def __init__(self, window: int = 30):
        self.window = window

    def generate(self, history: Sequence[Draw5D]) -> Pick5D:
        recent = _recent(history, self.window)
        if not recent:
            return (0, 0, 0, 0, 0)
        return tuple(_cold_digit(recent, position) for position in range(5))  # type: ignore[return-value]


class Omission5DStrategy:
    name = "五位遗漏策略"

    def __init__(self, window: int = 30):
        self.window = window

    def generate(self, history: Sequence[Draw5D]) -> Pick5D:
        recent = _recent(history, self.window)
        if not recent:
            return (0, 0, 0, 0, 0)
        return tuple(_longest_omission_digit(recent, position) for position in range(5))  # type: ignore[return-value]


def _recent(history: Sequence[Draw5D], window: int) -> Tuple[Draw5D, ...]:
    if window <= 0:
        raise ValueError("window 必须大于0")
    return tuple(history[-window:])


def _hot_digit(draws: Sequence[Draw5D], position: int) -> int:
    counts = _position_counts(draws, position)
    return min(range(10), key=lambda digit: (-counts[digit], digit))


def _cold_digit(draws: Sequence[Draw5D], position: int) -> int:
    counts = _position_counts(draws, position)
    return min(range(10), key=lambda digit: (counts[digit], digit))


def _longest_omission_digit(draws: Sequence[Draw5D], position: int) -> int:
    reversed_draws = list(reversed(draws))
    best_digit = 0
    best_distance = -1
    for digit in range(10):
        distance = _distance_from_latest(reversed_draws, position, digit)
        if distance > best_distance:
            best_digit = digit
            best_distance = distance
    return best_digit


def _position_counts(draws: Sequence[Draw5D], position: int) -> Counter:
    return Counter(draw.numbers[position] for draw in draws)


def _distance_from_latest(draws_newest_first: Sequence[Draw5D], position: int, digit: int) -> int:
    for index, draw in enumerate(draws_newest_first):
        if draw.numbers[position] == digit:
            return index
    return len(draws_newest_first)
