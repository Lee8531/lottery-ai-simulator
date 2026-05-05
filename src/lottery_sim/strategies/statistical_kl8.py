from collections import Counter
from typing import Sequence, Tuple

from lottery_sim.models import DrawKL8, Kl8Pick


class HotKl8Strategy:
    name = "快乐8热号策略"

    def __init__(self, pick_size: int = 10, window: int = 30):
        self.pick_size = pick_size
        self.window = window

    def generate(self, history: Sequence[DrawKL8]) -> Kl8Pick:
        recent = _recent(history, self.window)
        if not recent:
            return _default_pick(self.pick_size)
        return Kl8Pick(_select_by_count(_number_counts(recent), self.pick_size, hot=True))


class ColdKl8Strategy:
    name = "快乐8冷号策略"

    def __init__(self, pick_size: int = 10, window: int = 30):
        self.pick_size = pick_size
        self.window = window

    def generate(self, history: Sequence[DrawKL8]) -> Kl8Pick:
        recent = _recent(history, self.window)
        if not recent:
            return _default_pick(self.pick_size)
        return Kl8Pick(_select_by_count(_number_counts(recent), self.pick_size, hot=False))


class OmissionKl8Strategy:
    name = "快乐8遗漏策略"

    def __init__(self, pick_size: int = 10, window: int = 30):
        self.pick_size = pick_size
        self.window = window

    def generate(self, history: Sequence[DrawKL8]) -> Kl8Pick:
        recent = _recent(history, self.window)
        if not recent:
            return _default_pick(self.pick_size)
        newest_first = tuple(reversed(recent))
        selected = sorted(
            range(1, 81),
            key=lambda value: (-_distance_from_latest(newest_first, value), value),
        )[:self.pick_size]
        return Kl8Pick(tuple(sorted(selected)))


def _recent(history: Sequence[DrawKL8], window: int) -> Tuple[DrawKL8, ...]:
    if window <= 0:
        raise ValueError("window 必须大于0")
    return tuple(history[-window:])


def _default_pick(pick_size: int) -> Kl8Pick:
    if not 1 <= pick_size <= 10:
        raise ValueError("快乐8玩法必须在选一到选十之间")
    return Kl8Pick(tuple(range(1, pick_size + 1)))


def _number_counts(draws: Sequence[DrawKL8]) -> Counter:
    counts: Counter = Counter()
    for draw in draws:
        counts.update(draw.numbers)
    return counts


def _select_by_count(counts: Counter, pick_size: int, hot: bool) -> Tuple[int, ...]:
    if hot:
        selected = sorted(range(1, 81), key=lambda value: (-counts[value], value))[:pick_size]
    else:
        selected = sorted(range(1, 81), key=lambda value: (counts[value], value))[:pick_size]
    return tuple(sorted(selected))


def _distance_from_latest(draws: Sequence[DrawKL8], value: int) -> int:
    for index, draw in enumerate(draws):
        if value in draw.numbers:
            return index
    return len(draws)
