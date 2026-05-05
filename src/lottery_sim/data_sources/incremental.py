from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, List, Sequence, Tuple


@dataclass(frozen=True)
class IncrementalUpdateResult:
    output_path: Path
    previous_latest_issue: str
    latest_issue: str
    added_count: int
    total_count: int

    @property
    def is_latest(self) -> bool:
        return self.added_count == 0


def merge_incremental_draws(existing: Sequence[Any], incoming: Iterable[Any]) -> Tuple[List[Any], List[Any]]:
    by_issue = {draw.issue: draw for draw in existing}
    added: List[Any] = []

    for draw in incoming:
        if draw.issue in by_issue:
            continue
        by_issue[draw.issue] = draw
        added.append(draw)

    merged = sorted(by_issue.values(), key=lambda draw: int(draw.issue))
    added = sorted(added, key=lambda draw: int(draw.issue))
    return merged, added


def update_draws_csv(
    path: Path,
    source_draws: Sequence[Any],
    load_csv: Callable[[Path], List[Any]],
    save_csv: Callable[[Iterable[Any], Path], None],
) -> IncrementalUpdateResult:
    output_path = Path(path)
    existing = load_csv(output_path) if output_path.exists() else []
    previous_latest_issue = _latest_issue(existing)
    merged, added = merge_incremental_draws(existing, source_draws)

    if added or not output_path.exists():
        save_csv(merged, output_path)

    return IncrementalUpdateResult(
        output_path=output_path,
        previous_latest_issue=previous_latest_issue,
        latest_issue=_latest_issue(merged),
        added_count=len(added),
        total_count=len(merged),
    )


def render_incremental_update_result(game_name: str, result: IncrementalUpdateResult) -> str:
    lines = [
        f"{game_name}开奖数据增量更新",
        f"输出文件：{result.output_path}",
        f"更新前最新期号：{result.previous_latest_issue or '-'}",
        f"当前最新期号：{result.latest_issue or '-'}",
        f"新增期数：{result.added_count}",
        f"总期数：{result.total_count}",
    ]
    if result.is_latest:
        lines.append("状态：已是最新")
    else:
        lines.append("状态：已追加新开奖")
    return "\n".join(lines)


def _latest_issue(draws: Sequence[Any]) -> str:
    if not draws:
        return ""
    return max((draw.issue for draw in draws), key=lambda issue: int(issue))
