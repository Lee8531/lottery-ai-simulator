from collections import Counter
from typing import Sequence, Tuple

from lottery_sim.models import Draw3D, Pick3D


class Hot3DStrategy:
    name = "热号策略"

    def __init__(self, window: int = 30):
        self.window = window

    def generate(self, history: Sequence[Draw3D]) -> Pick3D:
        recent = _recent(history, self.window)
        if not recent:
            return (0, 0, 0)
        return tuple(_hot_digit(recent, position) for position in range(3))  # type: ignore[return-value]


class Cold3DStrategy:
    name = "冷号策略"

    def __init__(self, window: int = 30):
        self.window = window

    def generate(self, history: Sequence[Draw3D]) -> Pick3D:
        recent = _recent(history, self.window)
        if not recent:
            return (0, 0, 0)
        return tuple(_cold_digit(recent, position) for position in range(3))  # type: ignore[return-value]


class Omission3DStrategy:
    name = "遗漏策略"

    def __init__(self, window: int = 30):
        self.window = window

    def generate(self, history: Sequence[Draw3D]) -> Pick3D:
        recent = _recent(history, self.window)
        if not recent:
            return (0, 0, 0)
        return tuple(_longest_omission_digit(recent, position) for position in range(3))  # type: ignore[return-value]


class SumNearest3DStrategy:
    name = "和值策略"

    def __init__(self, window: int = 30):
        self.window = window

    def generate(self, history: Sequence[Draw3D]) -> Pick3D:
        recent = _recent(history, self.window)
        if not recent:
            return (0, 0, 0)

        average_sum = sum(sum(draw.numbers) for draw in recent) / len(recent)
        target_sum = int(average_sum + 0.5)
        return _first_pick_nearest_sum(target_sum)


def _recent(history: Sequence[Draw3D], window: int) -> Tuple[Draw3D, ...]:
    if window <= 0:
        raise ValueError("window 必须大于0")
    return tuple(history[-window:])


def _hot_digit(draws: Sequence[Draw3D], position: int) -> int:
    counts = _position_counts(draws, position)
    return min(range(10), key=lambda digit: (-counts[digit], digit))


def _cold_digit(draws: Sequence[Draw3D], position: int) -> int:
    counts = _position_counts(draws, position)
    return min(range(10), key=lambda digit: (counts[digit], digit))


def _longest_omission_digit(draws: Sequence[Draw3D], position: int) -> int:
    reversed_draws = list(reversed(draws))
    best_digit = 0
    best_distance = -1
    for digit in range(10):
        distance = _distance_from_latest(reversed_draws, position, digit)
        if distance > best_distance:
            best_digit = digit
            best_distance = distance
    return best_digit


def _position_counts(draws: Sequence[Draw3D], position: int) -> Counter:
    return Counter(draw.numbers[position] for draw in draws)


def _distance_from_latest(draws_newest_first: Sequence[Draw3D], position: int, digit: int) -> int:
    for index, draw in enumerate(draws_newest_first):
        if draw.numbers[position] == digit:
            return index
    return len(draws_newest_first)


def _first_pick_nearest_sum(target_sum: int) -> Pick3D:
    best_pick = (0, 0, 0)
    best_distance = 100
    for a in range(10):
        for b in range(10):
            for c in range(10):
                distance = abs((a + b + c) - target_sum)
                if distance < best_distance:
                    best_pick = (a, b, c)
                    best_distance = distance
                    if best_distance == 0:
                        return best_pick
    return best_pick
