import csv
import re
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional
from urllib.request import Request, urlopen

from lottery_sim.models import Draw3D, Pick3D


DEFAULT_17500_3D_ASC_URL = "http://data.17500.cn/3d_asc.txt"

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_ISSUE_RE = re.compile(r"^\d{5,8}$")


def fetch_17500_text(url: str, timeout: int = 20) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            )
        },
    )
    with urlopen(request, timeout=timeout) as response:
        raw = response.read()
    for encoding in ("utf-8", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def fetch_17500_3d_text(url: str = DEFAULT_17500_3D_ASC_URL, timeout: int = 20) -> str:
    return fetch_17500_text(url=url, timeout=timeout)


def parse_17500_3d_text(text: str) -> List[Draw3D]:
    return parse_17500_pick3_text(text, source="17500")


def parse_17500_pick3_text(text: str, source: str) -> List[Draw3D]:
    by_issue = {}
    for raw_line in text.splitlines():
        draw = _parse_line(raw_line, source=source)
        if draw is None:
            continue
        by_issue.setdefault(draw.issue, draw)
    return sorted(by_issue.values(), key=lambda draw: int(draw.issue))


def save_draws_csv(draws: Iterable[Draw3D], path: Path) -> None:
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


def load_draws_csv(path: Path) -> List[Draw3D]:
    with Path(path).open("r", encoding="utf-8", newline="") as f:
        rows = csv.DictReader(f)
        return [
            Draw3D(
                issue=row["issue"],
                draw_date=row["draw_date"],
                numbers=_parse_number_token(row["number"]),
                source=row.get("source") or "local",
            )
            for row in rows
        ]


def _parse_line(raw_line: str, source: str) -> Optional[Draw3D]:
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

    return Draw3D(issue=issue, draw_date=draw_date, numbers=numbers, source=source)


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


def _find_numbers_after_date(tokens: List[str], start: int) -> Optional[Pick3D]:
    if start >= len(tokens):
        return None

    first = tokens[start].strip()
    if first in {"", "-", "--", "---"}:
        return None

    if re.fullmatch(r"\d{3}", first):
        return _parse_number_token(first)

    next_three = tokens[start:start + 3]
    if len(next_three) == 3 and all(re.fullmatch(r"\d", token) for token in next_three):
        return tuple(int(token) for token in next_three)  # type: ignore[return-value]

    compact = "".join(re.findall(r"\d", first))
    if len(compact) == 3:
        return _parse_number_token(compact)

    return None


def _parse_number_token(token: str) -> Pick3D:
    compact = "".join(re.findall(r"\d", token))
    if len(compact) != 3:
        raise ValueError(f"福彩3D号码必须是3位数字: {token}")
    return tuple(int(ch) for ch in compact)  # type: ignore[return-value]


def _valid_date(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return False
    return True
