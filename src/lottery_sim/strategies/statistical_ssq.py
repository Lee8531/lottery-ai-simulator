from collections import Counter
from typing import Sequence, Tuple

from lottery_sim.models import DrawSSQ, SsqPick


class HotSsqStrategy:
    name = "双色球热号策略"

    def __init__(self, window: int = 30):
        self.window = window

    def generate(self, history: Sequence[DrawSSQ]) -> SsqPick:
        recent = _recent(history, self.window)
        if not recent:
            return _default_pick()
        return SsqPick(
            red=_select_by_count(_red_counts(recent), range(1, 34), 6, hot=True),
            blue=_select_one_by_count(_blue_counts(recent), range(1, 17), hot=True),
        )


class ColdSsqStrategy:
    name = "双色球冷号策略"

    def __init__(self, window: int = 30):
        self.window = window

    def generate(self, history: Sequence[DrawSSQ]) -> SsqPick:
        recent = _recent(history, self.window)
        if not recent:
            return _default_pick()
        return SsqPick(
            red=_select_by_count(_red_counts(recent), range(1, 34), 6, hot=False),
            blue=_select_one_by_count(_blue_counts(recent), range(1, 17), hot=False),
        )


class OmissionSsqStrategy:
    name = "双色球遗漏策略"

    def __init__(self, window: int = 30):
        self.window = window

    def generate(self, history: Sequence[DrawSSQ]) -> SsqPick:
        recent = _recent(history, self.window)
        if not recent:
            return _default_pick()
        newest_first = tuple(reversed(recent))
        return SsqPick(
            red=_select_by_omission(newest_first, range(1, 34), 6, is_red=True),
            blue=_select_by_omission(newest_first, range(1, 17), 1, is_red=False)[0],
        )


def _recent(history: Sequence[DrawSSQ], window: int) -> Tuple[DrawSSQ, ...]:
    if window <= 0:
        raise ValueError("window 必须大于0")
    return tuple(history[-window:])


def _default_pick() -> SsqPick:
    return SsqPick((1, 2, 3, 4, 5, 6), 1)


def _red_counts(draws: Sequence[DrawSSQ]) -> Counter:
    counts: Counter = Counter()
    for draw in draws:
        counts.update(draw.numbers.red)
    return counts


def _blue_counts(draws: Sequence[DrawSSQ]) -> Counter:
    return Counter(draw.numbers.blue for draw in draws)


def _select_by_count(counts: Counter, values: range, size: int, hot: bool) -> Tuple[int, ...]:
    if hot:
        selected = sorted(values, key=lambda value: (-counts[value], value))[:size]
    else:
        selected = sorted(values, key=lambda value: (counts[value], value))[:size]
    return tuple(sorted(selected))


def _select_one_by_count(counts: Counter, values: range, hot: bool) -> int:
    if hot:
        return min(values, key=lambda value: (-counts[value], value))
    return min(values, key=lambda value: (counts[value], value))


def _select_by_omission(
    newest_first: Sequence[DrawSSQ],
    values: range,
    size: int,
    is_red: bool,
) -> Tuple[int, ...]:
    selected = sorted(
        values,
        key=lambda value: (-_distance_from_latest(newest_first, value, is_red), value),
    )[:size]
    return tuple(sorted(selected))


def _distance_from_latest(draws: Sequence[DrawSSQ], value: int, is_red: bool) -> int:
    for index, draw in enumerate(draws):
        if _draw_contains(draw, value, is_red):
            return index
    return len(draws)


def _draw_contains(draw: DrawSSQ, value: int, is_red: bool) -> bool:
    if is_red:
        return value in draw.numbers.red
    return draw.numbers.blue == value
