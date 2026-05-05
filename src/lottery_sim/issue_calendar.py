from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, Tuple


@dataclass(frozen=True)
class IssueRule:
    game_code: str
    draw_weekdays: Tuple[int, ...]
    year_digits: int
    sequence_digits: int
    note: str


@dataclass(frozen=True)
class NextIssue:
    issue: str
    draw_date: date


_RULES: Dict[str, IssueRule] = {
    "3d": IssueRule("3d", (0, 1, 2, 3, 4, 5, 6), 4, 3, "daily"),
    "pl3": IssueRule("pl3", (0, 1, 2, 3, 4, 5, 6), 4, 3, "daily"),
    "pl5": IssueRule("pl5", (0, 1, 2, 3, 4, 5, 6), 4, 3, "daily"),
    "kl8": IssueRule("kl8", (0, 1, 2, 3, 4, 5, 6), 4, 3, "daily"),
    "ssq": IssueRule("ssq", (1, 3, 6), 4, 3, "Tue/Thu/Sun"),
    "qlc": IssueRule("qlc", (0, 2, 4), 4, 3, "Mon/Wed/Fri"),
    "dlt": IssueRule("dlt", (0, 2, 5), 2, 3, "Mon/Wed/Sat"),
    "qxc": IssueRule("qxc", (1, 4, 6), 2, 3, "Tue/Fri/Sun"),
}


def get_issue_rule(game_code: str) -> IssueRule:
    try:
        return _RULES[game_code]
    except KeyError as exc:
        raise ValueError(f"Unsupported game code: {game_code}") from exc


def is_scheduled_draw_date(game_code: str, value: date) -> bool:
    return value.weekday() in get_issue_rule(game_code).draw_weekdays


def next_scheduled_draw_date(game_code: str, after_date: date) -> date:
    current = after_date + timedelta(days=1)
    for _ in range(14):
        if is_scheduled_draw_date(game_code, current):
            return current
        current += timedelta(days=1)
    raise ValueError(f"No scheduled draw date found for {game_code} after {after_date}")


def next_issue_from_latest_draw(game_code: str, latest_issue: str, latest_draw_date: str) -> NextIssue:
    latest_date = _parse_date(latest_draw_date)
    target_date = next_scheduled_draw_date(game_code, latest_date)
    return NextIssue(
        issue=_next_issue_number(get_issue_rule(game_code), latest_issue, latest_date, target_date),
        draw_date=target_date,
    )


def _next_issue_number(rule: IssueRule, latest_issue: str, latest_date: date, target_date: date) -> str:
    expected_length = rule.year_digits + rule.sequence_digits
    if len(latest_issue) != expected_length or not latest_issue.isdigit():
        return str(int(latest_issue) + 1).zfill(len(latest_issue))

    if target_date.year != latest_date.year:
        sequence = 1
    else:
        sequence = int(latest_issue[rule.year_digits:]) + 1

    year_prefix = str(target_date.year)[-rule.year_digits:]
    return f"{year_prefix}{sequence:0{rule.sequence_digits}d}"


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()
