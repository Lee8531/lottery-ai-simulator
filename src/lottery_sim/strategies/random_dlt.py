import random
from typing import Sequence

from lottery_sim.models import DltPick, DrawDLT


class RandomDltStrategy:
    name = "大乐透随机基线"

    def __init__(self, seed: int = 20260505):
        self._rng = random.Random(seed)

    def generate(self, history: Sequence[DrawDLT]) -> DltPick:
        front = tuple(sorted(self._rng.sample(range(1, 36), 5)))
        back = tuple(sorted(self._rng.sample(range(1, 13), 2)))
        return DltPick(front=front, back=back)  # type: ignore[arg-type]
