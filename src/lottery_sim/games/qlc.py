from typing import Tuple

from lottery_sim.models import QlcDrawNumbers, QlcPick


class QlcGame:
    name = "七乐彩"
    ticket_cost = 2
    # 一、二、三等奖为浮动奖，这里使用估算值保证历史模拟可以统一比较。
    prize_amounts = {
        "一等奖": 5_000_000,
        "二等奖": 100_000,
        "三等奖": 10_000,
        "四等奖": 200,
        "五等奖": 50,
        "六等奖": 10,
        "七等奖": 5,
        "未中奖": 0,
    }

    def validate_pick(self, pick: QlcPick) -> QlcPick:
        if len(pick.numbers) != 7:
            raise ValueError("七乐彩投注号码必须包含7个号码")
        if len(set(pick.numbers)) != 7:
            raise ValueError("七乐彩投注号码不能重复")
        if not all(isinstance(value, int) and 1 <= value <= 30 for value in pick.numbers):
            raise ValueError("七乐彩投注号码必须在1到30之间")
        return QlcPick(tuple(sorted(pick.numbers)))  # type: ignore[arg-type]

    def validate_draw(self, draw: QlcDrawNumbers) -> QlcDrawNumbers:
        if len(draw.basic) != 7:
            raise ValueError("七乐彩基本号码必须包含7个号码")
        if len(set(draw.basic)) != 7:
            raise ValueError("七乐彩基本号码不能重复")
        if not all(isinstance(value, int) and 1 <= value <= 30 for value in draw.basic):
            raise ValueError("七乐彩基本号码必须在1到30之间")
        if not isinstance(draw.special, int) or not 1 <= draw.special <= 30:
            raise ValueError("七乐彩特别号码必须在1到30之间")
        if draw.special in set(draw.basic):
            raise ValueError("七乐彩特别号码不能与基本号码重复")
        return QlcDrawNumbers(basic=tuple(sorted(draw.basic)), special=draw.special)  # type: ignore[arg-type]

    def match_counts(self, draw_numbers: QlcDrawNumbers, pick_numbers: QlcPick) -> Tuple[int, int]:
        draw = self.validate_draw(draw_numbers)
        pick = self.validate_pick(pick_numbers)
        pick_set = set(pick.numbers)
        basic_hits = len(set(draw.basic) & pick_set)
        special_hit = 1 if draw.special in pick_set else 0
        return basic_hits, special_hit

    def prize_level(self, draw_numbers: QlcDrawNumbers, pick_numbers: QlcPick) -> str:
        basic_hits, special_hit = self.match_counts(draw_numbers, pick_numbers)
        if basic_hits == 7:
            return "一等奖"
        if basic_hits == 6 and special_hit == 1:
            return "二等奖"
        if basic_hits == 6 and special_hit == 0:
            return "三等奖"
        if basic_hits == 5 and special_hit == 1:
            return "四等奖"
        if basic_hits == 5 and special_hit == 0:
            return "五等奖"
        if basic_hits == 4 and special_hit == 1:
            return "六等奖"
        if basic_hits == 4 and special_hit == 0:
            return "七等奖"
        return "未中奖"

    def payout(self, draw_numbers: QlcDrawNumbers, pick_numbers: QlcPick) -> int:
        return self.prize_amounts[self.prize_level(draw_numbers, pick_numbers)]
