from collections import Counter
from typing import Sequence, Tuple

from lottery_sim.models import DltPick, DrawDLT


class HotDltStrategy:
    name = "大乐透热号策略"

    def __init__(self, window: int = 30):
        self.window = window

    def generate(self, history: Sequence[DrawDLT]) -> DltPick:
        recent = _recent(history, self.window)
        if not recent:
            return _default_pick()
        return DltPick(
            front=_select_by_count(_front_counts(recent), range(1, 36), 5, hot=True),
            back=_select_by_count(_back_counts(recent), range(1, 13), 2, hot=True),
        )  # type: ignore[arg-type]


class ColdDltStrategy:
    name = "大乐透冷号策略"

    def __init__(self, window: int = 30):
        self.window = window

    def generate(self, history: Sequence[DrawDLT]) -> DltPick:
        recent = _recent(history, self.window)
        if not recent:
            return _default_pick()
        return DltPick(
            front=_select_by_count(_front_counts(recent), range(1, 36), 5, hot=False),
            back=_select_by_count(_back_counts(recent), range(1, 13), 2, hot=False),
        )  # type: ignore[arg-type]


class OmissionDltStrategy:
    name = "大乐透遗漏策略"

    def __init__(self, window: int = 30):
        self.window = window

    def generate(self, history: Sequence[DrawDLT]) -> DltPick:
        recent = _recent(history, self.window)
        if not recent:
            return _default_pick()
        newest_first = tuple(reversed(recent))
        return DltPick(
            front=_select_by_omission(newest_first, range(1, 36), 5, is_front=True),
            back=_select_by_omission(newest_first, range(1, 13), 2, is_front=False),
        )  # type: ignore[arg-type]


def _recent(history: Sequence[DrawDLT], window: int) -> Tuple[DrawDLT, ...]:
    if window <= 0:
        raise ValueError("window 必须大于0")
    return tuple(history[-window:])


def _default_pick() -> DltPick:
    return DltPick((1, 2, 3, 4, 5), (1, 2))


def _front_counts(draws: Sequence[DrawDLT]) -> Counter:
    counts: Counter = Counter()
    for draw in draws:
        counts.update(draw.numbers.front)
    return counts


def _back_counts(draws: Sequence[DrawDLT]) -> Counter:
    counts: Counter = Counter()
    for draw in draws:
        counts.update(draw.numbers.back)
    return counts


def _select_by_count(counts: Counter, values: range, size: int, hot: bool) -> Tuple[int, ...]:
    if hot:
        selected = sorted(values, key=lambda value: (-counts[value], value))[:size]
    else:
        selected = sorted(values, key=lambda value: (counts[value], value))[:size]
    return tuple(sorted(selected))


def _select_by_omission(
    newest_first: Sequence[DrawDLT],
    values: range,
    size: int,
    is_front: bool,
) -> Tuple[int, ...]:
    selected = sorted(
        values,
        key=lambda value: (-_distance_from_latest(newest_first, value, is_front), value),
    )[:size]
    return tuple(sorted(selected))


def _distance_from_latest(draws: Sequence[DrawDLT], value: int, is_front: bool) -> int:
    for index, draw in enumerate(draws):
        if _draw_contains(draw, value, is_front):
            return index
    return len(draws)


def _draw_contains(draw: DrawDLT, value: int, is_front: bool) -> bool:
    if is_front:
        return value in draw.numbers.front
    return value in draw.numbers.back
