from collections import Counter
from typing import Sequence, Tuple

from lottery_sim.models import DrawQLC, QlcPick


class HotQlcStrategy:
    name = "七乐彩热号策略"

    def __init__(self, window: int = 30):
        self.window = window

    def generate(self, history: Sequence[DrawQLC]) -> QlcPick:
        recent = _recent(history, self.window)
        if not recent:
            return _default_pick()
        return QlcPick(_select_by_count(_all_number_counts(recent), hot=True))


class ColdQlcStrategy:
    name = "七乐彩冷号策略"

    def __init__(self, window: int = 30):
        self.window = window

    def generate(self, history: Sequence[DrawQLC]) -> QlcPick:
        recent = _recent(history, self.window)
        if not recent:
            return _default_pick()
        return QlcPick(_select_by_count(_all_number_counts(recent), hot=False))


class OmissionQlcStrategy:
    name = "七乐彩遗漏策略"

    def __init__(self, window: int = 30):
        self.window = window

    def generate(self, history: Sequence[DrawQLC]) -> QlcPick:
        recent = _recent(history, self.window)
        if not recent:
            return _default_pick()
        newest_first = tuple(reversed(recent))
        selected = sorted(
            range(1, 31),
            key=lambda value: (-_distance_from_latest(newest_first, value), value),
        )[:7]
        return QlcPick(tuple(sorted(selected)))  # type: ignore[arg-type]


def _recent(history: Sequence[DrawQLC], window: int) -> Tuple[DrawQLC, ...]:
    if window <= 0:
        raise ValueError("window 必须大于0")
    return tuple(history[-window:])


def _default_pick() -> QlcPick:
    return QlcPick((1, 2, 3, 4, 5, 6, 7))


def _all_number_counts(draws: Sequence[DrawQLC]) -> Counter:
    counts: Counter = Counter()
    for draw in draws:
        counts.update(draw.numbers.basic)
        counts.update([draw.numbers.special])
    return counts


def _select_by_count(counts: Counter, hot: bool) -> Tuple[int, int, int, int, int, int, int]:
    if hot:
        selected = sorted(range(1, 31), key=lambda value: (-counts[value], value))[:7]
    else:
        selected = sorted(range(1, 31), key=lambda value: (counts[value], value))[:7]
    return tuple(sorted(selected))  # type: ignore[return-value]


def _distance_from_latest(draws: Sequence[DrawQLC], value: int) -> int:
    for index, draw in enumerate(draws):
        if value in draw.numbers.basic or value == draw.numbers.special:
            return index
    return len(draws)
