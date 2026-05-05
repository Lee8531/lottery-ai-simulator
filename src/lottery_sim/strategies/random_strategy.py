import random
from typing import Sequence

from lottery_sim.models import Draw3D, Pick3D


class Random3DStrategy:
    name = "随机基线"

    def __init__(self, seed: int = 20260505):
        self._rng = random.Random(seed)

    def generate(self, history: Sequence[Draw3D]) -> Pick3D:
        return (
            self._rng.randint(0, 9),
            self._rng.randint(0, 9),
            self._rng.randint(0, 9),
        )
