import random
from typing import Sequence

from lottery_sim.models import DrawQXC, QxcPick


class RandomQxcStrategy:
    name = "7星彩随机基线"

    def __init__(self, seed: int = 0):
        self._rng = random.Random(seed)

    def generate(self, history: Sequence[DrawQXC]) -> QxcPick:
        del history
        return QxcPick(
            front=tuple(self._rng.randint(0, 9) for _ in range(6)),  # type: ignore[arg-type]
            special=self._rng.randint(0, 14),
        )
