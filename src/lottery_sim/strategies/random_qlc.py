import random
from typing import Sequence

from lottery_sim.models import DrawQLC, QlcPick


class RandomQlcStrategy:
    name = "七乐彩随机基线"

    def __init__(self, seed: int = 0):
        self._rng = random.Random(seed)

    def generate(self, history: Sequence[DrawQLC]) -> QlcPick:
        del history
        return QlcPick(tuple(sorted(self._rng.sample(range(1, 31), 7))))  # type: ignore[arg-type]
