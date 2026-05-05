import random
from typing import Sequence

from lottery_sim.models import DrawSSQ, SsqPick


class RandomSsqStrategy:
    name = "双色球随机基线"

    def __init__(self, seed: int = 20260505):
        self._rng = random.Random(seed)

    def generate(self, history: Sequence[DrawSSQ]) -> SsqPick:
        red = tuple(sorted(self._rng.sample(range(1, 34), 6)))
        blue = self._rng.randint(1, 16)
        return SsqPick(red=red, blue=blue)  # type: ignore[arg-type]
