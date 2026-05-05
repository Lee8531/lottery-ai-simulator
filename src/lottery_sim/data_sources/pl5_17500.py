import csv
import re
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from lottery_sim.data_sources.fucai3d_17500 import fetch_17500_text
from lottery_sim.models import Draw5D, Pick5D


DEFAULT_17500_PL5_ASC_URL = "http://data.17500.cn/pl5_asc.txt"
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_ISSUE_RE = re.compile(r"^\d{5,8}$")


def fetch_17500_pl5_text(url: str = DEFAULT_17500_PL5_ASC_URL, timeout: int = 20) -> str:
    return fetch_17500_text(url=url, timeout=timeout)


def parse_17500_pl5_text(text: str) -> List[Draw5D]:
    by_issue = {}
    for raw_line in text.splitlines():
        draw = _parse_line(raw_line)
        if draw is None:
            continue
        by_issue.setdefault(draw.issue, draw)
    return sorted(by_issue.values(), key=lambda draw: int(draw.issue))


def save_pl5_draws_csv(draws: Iterable[Draw5D], path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["issue", "draw_date", "number", "source"])
        writer.writeheader()
        for draw in draws:
            writer.writerow({
                "issue": draw.issue,
                "draw_date": draw.draw_date,
                "number": draw.number_text,
                "source": draw.source,
            })


def load_pl5_draws_csv(path: Path) -> List[Draw5D]:
    with Path(path).open("r", encoding="utf-8", newline="") as f:
        rows = csv.DictReader(f)
        return [
            Draw5D(
                issue=row["issue"],
                draw_date=row["draw_date"],
                numbers=_parse_number_token(row["number"]),
                source=row.get("source") or "local",
            )
            for row in rows
        ]


def _parse_line(raw_line: str) -> Optional[Draw5D]:
    line = raw_line.strip()
    if not line or "期号" in line:
        return None

    tokens = re.split(r"[\s,\t]+", line)
    issue_index = _find_issue_index(tokens)
    if issue_index is None:
        return None

    issue = tokens[issue_index]
    date_index = _find_date_index(tokens, issue_index + 1)
    if date_index is None:
        return None

    draw_date = tokens[date_index]
    if not _valid_date(draw_date):
        return None

    numbers = _find_numbers_after_date(tokens, date_index + 1)
    if numbers is None:
        return None
    return Draw5D(issue=issue, draw_date=draw_date, numbers=numbers)


def _find_issue_index(tokens: List[str]) -> Optional[int]:
    for index, token in enumerate(tokens):
        if _ISSUE_RE.match(token):
            return index
    return None


def _find_date_index(tokens: List[str], start: int) -> Optional[int]:
    for index in range(start, len(tokens)):
        if _DATE_RE.match(tokens[index]):
            return index
    return None


def _find_numbers_after_date(tokens: List[str], start: int) -> Optional[Pick5D]:
    values = []
    for token in tokens[start:]:
        if re.fullmatch(r"\d", token):
            values.append(int(token))
        else:
            break
        if len(values) == 5:
            break
    if len(values) != 5:
        return None
    return tuple(values)  # type: ignore[return-value]


def _parse_number_token(token: str) -> Pick5D:
    value = token.strip()
    if not re.fullmatch(r"\d{5}", value):
        raise ValueError(f"排列五号码格式不合法: {token}")
    return tuple(int(char) for char in value)  # type: ignore[return-value]


def _valid_date(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return False
    return True
