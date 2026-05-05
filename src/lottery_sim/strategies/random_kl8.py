import random
from typing import Sequence

from lottery_sim.models import DrawKL8, Kl8Pick


class RandomKl8Strategy:
    name = "快乐8随机基线"

    def __init__(self, pick_size: int = 10, seed: int = 0):
        self.pick_size = pick_size
        self._rng = random.Random(seed)

    def generate(self, history: Sequence[DrawKL8]) -> Kl8Pick:
        del history
        return Kl8Pick(tuple(sorted(self._rng.sample(range(1, 81), self.pick_size))))
