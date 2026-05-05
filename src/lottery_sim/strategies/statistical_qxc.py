from collections import Counter
from typing import Sequence, Tuple

from lottery_sim.models import DrawQXC, QxcPick


class HotQxcStrategy:
    name = "7星彩热号策略"

    def __init__(self, window: int = 30):
        self.window = window

    def generate(self, history: Sequence[DrawQXC]) -> QxcPick:
        recent = _recent(history, self.window)
        if not recent:
            return _minimum_pick()
        return QxcPick(
            front=tuple(_hot_front_digit(recent, position) for position in range(6)),  # type: ignore[arg-type]
            special=_hot_special(recent),
        )


class ColdQxcStrategy:
    name = "7星彩冷号策略"

    def __init__(self, window: int = 30):
        self.window = window

    def generate(self, history: Sequence[DrawQXC]) -> QxcPick:
        recent = _recent(history, self.window)
        if not recent:
            return _minimum_pick()
        return QxcPick(
            front=tuple(_cold_front_digit(recent, position) for position in range(6)),  # type: ignore[arg-type]
            special=_cold_special(recent),
        )


class OmissionQxcStrategy:
    name = "7星彩遗漏策略"

    def __init__(self, window: int = 30):
        self.window = window

    def generate(self, history: Sequence[DrawQXC]) -> QxcPick:
        recent = _recent(history, self.window)
        if not recent:
            return _minimum_pick()
        reversed_draws = tuple(reversed(recent))
        return QxcPick(
            front=tuple(
                _longest_front_omission_digit(reversed_draws, position)
                for position in range(6)
            ),  # type: ignore[arg-type]
            special=_longest_special_omission(reversed_draws),
        )


def _minimum_pick() -> QxcPick:
    return QxcPick((0, 0, 0, 0, 0, 0), 0)


def _recent(history: Sequence[DrawQXC], window: int) -> Tuple[DrawQXC, ...]:
    if window <= 0:
        raise ValueError("window 必须大于0")
    return tuple(history[-window:])


def _hot_front_digit(draws: Sequence[DrawQXC], position: int) -> int:
    counts = _front_counts(draws, position)
    return min(range(10), key=lambda digit: (-counts[digit], digit))


def _cold_front_digit(draws: Sequence[DrawQXC], position: int) -> int:
    counts = _front_counts(draws, position)
    return min(range(10), key=lambda digit: (counts[digit], digit))


def _hot_special(draws: Sequence[DrawQXC]) -> int:
    counts = _special_counts(draws)
    return min(range(15), key=lambda digit: (-counts[digit], digit))


def _cold_special(draws: Sequence[DrawQXC]) -> int:
    counts = _special_counts(draws)
    return min(range(15), key=lambda digit: (counts[digit], digit))


def _longest_front_omission_digit(draws_newest_first: Sequence[DrawQXC], position: int) -> int:
    return _longest_omission_digit(
        range(10),
        lambda draw: draw.numbers.front[position],
        draws_newest_first,
    )


def _longest_special_omission(draws_newest_first: Sequence[DrawQXC]) -> int:
    return _longest_omission_digit(
        range(15),
        lambda draw: draw.numbers.special,
        draws_newest_first,
    )


def _longest_omission_digit(digits, value_getter, draws_newest_first: Sequence[DrawQXC]) -> int:
    best_digit = 0
    best_distance = -1
    for digit in digits:
        distance = _distance_from_latest(draws_newest_first, value_getter, digit)
        if distance > best_distance:
            best_digit = digit
            best_distance = distance
    return best_digit


def _front_counts(draws: Sequence[DrawQXC], position: int) -> Counter:
    return Counter(draw.numbers.front[position] for draw in draws)


def _special_counts(draws: Sequence[DrawQXC]) -> Counter:
    return Counter(draw.numbers.special for draw in draws)


def _distance_from_latest(draws_newest_first: Sequence[DrawQXC], value_getter, digit: int) -> int:
    for index, draw in enumerate(draws_newest_first):
        if value_getter(draw) == digit:
            return index
    return len(draws_newest_first)
