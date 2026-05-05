from lottery_sim.models import Pick3D


class Pick3DirectGame:
    name = "三位直选"
    ticket_cost = 2
    direct_prize = 1040

    def validate_pick(self, pick: Pick3D) -> Pick3D:
        if len(pick) != 3:
            raise ValueError(f"{self.name}号码必须包含3位")
        for value in pick:
            if not isinstance(value, int) or value < 0 or value > 9:
                raise ValueError(f"{self.name}每一位都必须是0到9的整数")
        return pick

    def match(self, draw_numbers: Pick3D, pick_numbers: Pick3D) -> bool:
        return self.validate_pick(draw_numbers) == self.validate_pick(pick_numbers)

    def payout(self, draw_numbers: Pick3D, pick_numbers: Pick3D) -> int:
        if self.match(draw_numbers, pick_numbers):
            return self.direct_prize
        return 0
