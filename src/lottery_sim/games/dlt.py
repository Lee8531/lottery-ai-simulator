from typing import Tuple

from lottery_sim.models import DltPick


class DltGame:
    name = "大乐透"
    ticket_cost = 2
    # 一、二等奖为浮动奖，这里用固定估算值保持历史模拟口径可比较。
    prize_amounts = {
        "一等奖": 10_000_000,
        "二等奖": 100_000,
        "三等奖": 10_000,
        "四等奖": 3000,
        "五等奖": 300,
        "六等奖": 200,
        "七等奖": 100,
        "八等奖": 15,
        "九等奖": 5,
        "未中奖": 0,
    }

    def validate_pick(self, pick: DltPick) -> DltPick:
        if len(pick.front) != 5:
            raise ValueError("大乐透前区必须包含5个号码")
        if len(set(pick.front)) != 5:
            raise ValueError("大乐透前区不能重复")
        if not all(isinstance(value, int) and 1 <= value <= 35 for value in pick.front):
            raise ValueError("大乐透前区必须在1到35之间")
        if len(pick.back) != 2:
            raise ValueError("大乐透后区必须包含2个号码")
        if len(set(pick.back)) != 2:
            raise ValueError("大乐透后区不能重复")
        if not all(isinstance(value, int) and 1 <= value <= 12 for value in pick.back):
            raise ValueError("大乐透后区必须在1到12之间")
        return DltPick(
            front=tuple(sorted(pick.front)),
            back=tuple(sorted(pick.back)),
        )  # type: ignore[arg-type]

    def match_counts(self, draw_numbers: DltPick, pick_numbers: DltPick) -> Tuple[int, int]:
        draw = self.validate_pick(draw_numbers)
        pick = self.validate_pick(pick_numbers)
        front_hits = len(set(draw.front) & set(pick.front))
        back_hits = len(set(draw.back) & set(pick.back))
        return front_hits, back_hits

    def prize_level(self, draw_numbers: DltPick, pick_numbers: DltPick) -> str:
        front_hits, back_hits = self.match_counts(draw_numbers, pick_numbers)
        if front_hits == 5 and back_hits == 2:
            return "一等奖"
        if front_hits == 5 and back_hits == 1:
            return "二等奖"
        if front_hits == 5 and back_hits == 0:
            return "三等奖"
        if front_hits == 4 and back_hits == 2:
            return "四等奖"
        if front_hits == 4 and back_hits == 1:
            return "五等奖"
        if front_hits == 3 and back_hits == 2:
            return "六等奖"
        if front_hits == 4 and back_hits == 0:
            return "七等奖"
        if (front_hits == 3 and back_hits == 1) or (front_hits == 2 and back_hits == 2):
            return "八等奖"
        if (
            (front_hits == 3 and back_hits == 0)
            or (front_hits == 2 and back_hits == 1)
            or (front_hits == 1 and back_hits == 2)
            or (front_hits == 0 and back_hits == 2)
        ):
            return "九等奖"
        return "未中奖"

    def payout(self, draw_numbers: DltPick, pick_numbers: DltPick) -> int:
        return self.prize_amounts[self.prize_level(draw_numbers, pick_numbers)]
