from lottery_sim.models import Pick5D


class Pick5DirectGame:
    name = "五位直选"
    ticket_cost = 2
    direct_prize = 100_000

    def validate_pick(self, pick: Pick5D) -> Pick5D:
        if len(pick) != 5:
            raise ValueError(f"{self.name}号码必须包含5位")
        for value in pick:
            if not isinstance(value, int) or value < 0 or value > 9:
                raise ValueError(f"{self.name}每一位都必须是0到9的整数")
        return pick

    def match(self, draw_numbers: Pick5D, pick_numbers: Pick5D) -> bool:
        return self.validate_pick(draw_numbers) == self.validate_pick(pick_numbers)

    def payout(self, draw_numbers: Pick5D, pick_numbers: Pick5D) -> int:
        if self.match(draw_numbers, pick_numbers):
            return self.direct_prize
        return 0
