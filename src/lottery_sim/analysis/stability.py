from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

from lottery_sim.analysis.metrics import winning_bet_count
from lottery_sim.models import BacktestResult, BetResult


@dataclass(frozen=True)
class SegmentMetric:
    segment: str
    total_bets: int
    total_cost: int
    total_payout: int
    direct_hits: int

    @property
    def roi(self) -> float:
        if self.total_cost == 0:
            return 0.0
        return self.total_payout / self.total_cost


@dataclass(frozen=True)
class SeedSensitivity:
    seed_count: int
    average_roi: float
    min_roi: float
    max_roi: float
    average_direct_hits: float


def summarize_result_by_issue_year(result: BacktestResult) -> List[SegmentMetric]:
    grouped = {}
    for bet in result.bet_results:
        year = _issue_year(bet.issue)
        grouped.setdefault(year, []).append(bet)

    metrics = []
    for year in sorted(grouped):
        metrics.append(_summarize_bets(year, grouped[year]))
    return metrics


def summarize_seed_sensitivity(seed_results: Iterable[Tuple[int, BacktestResult]]) -> SeedSensitivity:
    rows = list(seed_results)
    if not rows:
        return SeedSensitivity(
            seed_count=0,
            average_roi=0.0,
            min_roi=0.0,
            max_roi=0.0,
            average_direct_hits=0.0,
        )

    rois = [result.roi for _, result in rows]
    hits = [winning_bet_count(result) for _, result in rows]
    return SeedSensitivity(
        seed_count=len(rows),
        average_roi=sum(rois) / len(rois),
        min_roi=min(rois),
        max_roi=max(rois),
        average_direct_hits=sum(hits) / len(hits),
    )


def _issue_year(issue: str) -> str:
    if len(issue) == 5 and issue.isdigit():
        return f"20{issue[:2]}"
    if len(issue) < 4 or not issue[:4].isdigit():
        return "unknown"
    return issue[:4]


def _summarize_bets(segment: str, bets: Sequence[BetResult]) -> SegmentMetric:
    return SegmentMetric(
        segment=segment,
        total_bets=len(bets),
        total_cost=sum(bet.cost for bet in bets),
        total_payout=sum(bet.payout for bet in bets),
        direct_hits=sum(1 for bet in bets if bet.hit),
    )
