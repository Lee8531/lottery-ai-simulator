from lottery_sim.models import BacktestResult


NO_PRIZE_LABELS = {"miss", "未中奖"}


def winning_bet_count(result: BacktestResult) -> int:
    if result.bet_results:
        return sum(1 for bet in result.bet_results if bet.hit)
    if "direct_hit" in result.hit_distribution:
        return result.hit_distribution["direct_hit"]
    return sum(
        count
        for label, count in result.hit_distribution.items()
        if label not in NO_PRIZE_LABELS
    )


def uses_direct_hit_metric(result: BacktestResult) -> bool:
    return set(result.hit_distribution) <= {"direct_hit", "miss"}
