import random
from typing import Sequence

from lottery_sim.models import Draw5D, Pick5D


class Random5DStrategy:
    name = "五位随机基线"

    def __init__(self, seed: int = 20260505):
        self._rng = random.Random(seed)

    def generate(self, history: Sequence[Draw5D]) -> Pick5D:
        return tuple(self._rng.randint(0, 9) for _ in range(5))  # type: ignore[return-value]
