from typing import Dict

from lottery_sim.models import Kl8Pick


_PICK_SIZE_LABELS = {
    1: "一",
    2: "二",
    3: "三",
    4: "四",
    5: "五",
    6: "六",
    7: "七",
    8: "八",
    9: "九",
    10: "十",
}

_PRIZE_TABLE = {
    1: {1: 4.5},
    2: {2: 19},
    3: {3: 52, 2: 3},
    4: {4: 93, 3: 5, 2: 3},
    5: {5: 1000, 4: 20, 3: 3},
    6: {6: 2880, 5: 30, 4: 10, 3: 3},
    7: {7: 8500, 6: 300, 5: 30, 4: 4, 0: 2},
    8: {8: 50_000, 7: 800, 6: 80, 5: 10, 4: 3, 0: 2},
    9: {9: 250_000, 8: 2000, 7: 225, 6: 22, 5: 5, 4: 3, 0: 2},
    10: {10: 5_000_000, 9: 8000, 8: 720, 7: 80, 6: 5, 5: 3, 0: 2},
}


class Kl8Game:
    ticket_cost = 2

    def __init__(self, pick_size: int = 10):
        if pick_size not in _PRIZE_TABLE:
            raise ValueError("快乐8玩法必须在选一到选十之间")
        self.pick_size = pick_size
        self.name = f"快乐8选{_PICK_SIZE_LABELS[pick_size]}"
        self.prize_amounts: Dict[int, float] = _PRIZE_TABLE[pick_size]

    def validate_pick(self, pick: Kl8Pick) -> Kl8Pick:
        if len(pick.numbers) != self.pick_size:
            raise ValueError(f"{self.name}投注号码必须包含{self.pick_size}个号码")
        if len(set(pick.numbers)) != self.pick_size:
            raise ValueError("快乐8投注号码不能重复")
        if not all(isinstance(value, int) and 1 <= value <= 80 for value in pick.numbers):
            raise ValueError("快乐8投注号码必须在1到80之间")
        return Kl8Pick(tuple(sorted(pick.numbers)))

    def validate_draw(self, draw_numbers) -> tuple:
        numbers = tuple(draw_numbers)
        if len(numbers) != 20:
            raise ValueError("快乐8开奖号码必须包含20个号码")
        if len(set(numbers)) != 20:
            raise ValueError("快乐8开奖号码不能重复")
        if not all(isinstance(value, int) and 1 <= value <= 80 for value in numbers):
            raise ValueError("快乐8开奖号码必须在1到80之间")
        return tuple(sorted(numbers))

    def match_count(self, draw_numbers, pick_numbers: Kl8Pick) -> int:
        draw = set(self.validate_draw(draw_numbers))
        pick = self.validate_pick(pick_numbers)
        return len(draw & set(pick.numbers))

    def prize_level(self, draw_numbers, pick_numbers: Kl8Pick) -> str:
        hits = self.match_count(draw_numbers, pick_numbers)
        if hits in self.prize_amounts:
            return f"中{hits}"
        return "未中奖"

    def payout(self, draw_numbers, pick_numbers: Kl8Pick) -> float:
        hits = self.match_count(draw_numbers, pick_numbers)
        return self.prize_amounts.get(hits, 0)
