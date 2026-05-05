from typing import List

from lottery_sim.data_sources.fucai3d_17500 import (
    fetch_17500_text,
    parse_17500_pick3_text,
)
from lottery_sim.models import Draw3D


DEFAULT_17500_PL3_ASC_URL = "http://data.17500.cn/pl3_asc.txt"


def fetch_17500_pl3_text(url: str = DEFAULT_17500_PL3_ASC_URL, timeout: int = 20) -> str:
    return fetch_17500_text(url=url, timeout=timeout)


def parse_17500_pl3_text(text: str) -> List[Draw3D]:
    return parse_17500_pick3_text(text, source="17500-pl3")
