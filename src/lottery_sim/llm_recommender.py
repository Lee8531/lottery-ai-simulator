#!/usr/bin/env python3
"""LLM-based lottery number recommender.

Uses OpenAI-compatible API (e.g. DeepSeek) to generate lottery number
recommendations. Falls back to ML model on API errors.
"""

import json
import os
import re
from collections import Counter
from typing import Any, List, Sequence, Tuple

import httpx

from lottery_sim.recommendations import Candidate


# Game rule descriptions used in the LLM prompt.
GAME_RULES: dict = {
    "3d": {
        "name": "福彩3D",
        "groups": [
            {"name": "第1位", "min": 0, "max": 9, "pick": 1},
            {"name": "第2位", "min": 0, "max": 9, "pick": 1},
            {"name": "第3位", "min": 0, "max": 9, "pick": 1},
        ],
    },
    "pl5": {
        "name": "排列五",
        "groups": [
            {"name": "第1位", "min": 0, "max": 9, "pick": 1},
            {"name": "第2位", "min": 0, "max": 9, "pick": 1},
            {"name": "第3位", "min": 0, "max": 9, "pick": 1},
            {"name": "第4位", "min": 0, "max": 9, "pick": 1},
            {"name": "第5位", "min": 0, "max": 9, "pick": 1},
        ],
    },
    "qlc": {
        "name": "七乐彩",
        "groups": [
            {"name": "基本号", "min": 1, "max": 30, "pick": 7},
        ],
    },
    "kl8": {
        "name": "快乐8",
        "groups": [
            {"name": "号码", "min": 1, "max": 80, "pick": 10},
        ],
    },
    "ssq": {
        "name": "双色球",
        "groups": [
            {"name": "红球", "min": 1, "max": 33, "pick": 6},
            {"name": "蓝球", "min": 1, "max": 16, "pick": 1},
        ],
    },
    "dlt": {
        "name": "大乐透",
        "groups": [
            {"name": "前区", "min": 1, "max": 35, "pick": 5},
            {"name": "后区", "min": 1, "max": 12, "pick": 2},
        ],
    },
}

# Maximum candidates per single LLM call — avoids finish_reason=length truncation
_MAX_BATCH = 3


def _llm_config_from_env() -> Tuple[str, str, str]:
    """Read LLM config from environment variables."""
    base_url = os.environ.get("LOTTERY_LLM_BASE_URL", "")
    model = os.environ.get("LOTTERY_LLM_MODEL", "")
    api_key = os.environ.get("LOTTERY_LLM_API_KEY", "")
    return base_url, model, api_key


def _build_stats_from_draws(draws: Sequence[Any], game_code: str, recent: int = 30) -> str:
    """Build a statistical summary of recent draws for the LLM prompt."""
    rule = GAME_RULES.get(game_code)
    if not rule:
        return "无历史统计数据"

    ordered = tuple(sorted(draws, key=lambda d: int(d.issue)))
    recent_draws = ordered[-recent:] if len(ordered) >= recent else ordered
    if not recent_draws:
        return "无历史数据"

    lines = [f"最近{len(recent_draws)}期开奖数据统计："]

    # Extract numbers per group
    adapter = _adapter_for_stats(game_code)
    group_counts: list = []
    for gi, group in enumerate(rule["groups"]):
        counter = Counter()
        for draw in recent_draws:
            nums = adapter(draw)[gi]
            counter.update(nums)
        total_draws = len(recent_draws)
        freq_items = sorted(counter.items(), key=lambda x: (-x[1], x[0]))
        top = freq_items[:max(group["pick"] * 2, 5)]
        freq_str = ", ".join(f"{n}出现{c}次({c/total_draws:.1%})" for n, c in top)
        lines.append(f"  {group['name']}({group['min']}-{group['max']}): {freq_str}")
        group_counts.append(counter)

    # Show last 5 draws
    lines.append("最近5期开奖号码：")
    for draw in recent_draws[-5:]:
        nums = adapter(draw)
        num_strs = []
        for gi, group in enumerate(rule["groups"]):
            ns = sorted(nums[gi]) if group["pick"] > 1 else list(nums[gi])
            num_strs.append(f"{group['name']}={','.join(str(n) for n in ns)}")
        lines.append(f"  期号{draw.issue}: {'; '.join(num_strs)}")

    return "\n".join(lines)


def _adapter_for_stats(game_code: str):
    """Return a function that extracts number groups from a draw object."""
    if game_code == "3d":
        def f(d): return tuple((v,) for v in d.numbers)
        return f
    if game_code == "pl5":
        def f(d): return tuple((v,) for v in d.numbers)
        return f
    if game_code == "qlc":
        def f(d): return (tuple(sorted((*d.numbers.basic, d.numbers.special))),)
        return f
    if game_code == "kl8":
        def f(d): return (tuple(sorted(d.numbers)),)
        return f
    if game_code == "ssq":
        def f(d): return (tuple(sorted(d.numbers.red)), (d.numbers.blue,))
        return f
    if game_code == "dlt":
        def f(d): return (tuple(sorted(d.numbers.front)), tuple(sorted(d.numbers.back)))
        return f
    raise ValueError(f"unsupported game: {game_code}")


def _build_prompt(draws: Sequence[Any], game_code: str, count: int) -> str:
    """Build the LLM prompt for number recommendation."""
    rule = GAME_RULES[game_code]
    game_name = rule["name"]

    group_descs = []
    for g in rule["groups"]:
        if g["pick"] == 1:
            group_descs.append(f"{g['name']}: 选1个数字，范围{g['min']}-{g['max']}")
        else:
            group_descs.append(f"{g['name']}: 选{g['pick']}个不重复数字，范围{g['min']}-{g['max']}")

    stats = _build_stats_from_draws(draws, game_code)

    prompt = f"""你是一个彩票号码分析助手。请根据历史数据统计，为{game_name}推荐{count}组号码。

游戏规则：
{chr(10).join('- ' + d for d in group_descs)}

{stats}

请严格按照以下JSON格式返回结果，不要添加任何其他文字：
{{"candidates": [{{"groups": [{{"name": "组名", "numbers": [数字列表]}}], "reason": "推荐理由"}}]}}

要求：
1. 推荐的号码必须在对应范围内
2. 多选组内号码不能重复
3. 每组推荐都要有推荐理由
4. 推荐{count}组不同的号码组合
5. 结合频率和遗漏数据分析给出推荐"""

    return prompt


def _normalize_groups(groups_data: list, game_code: str) -> list:
    """Normalize LLM response groups to match game rules.

    LLM may return all numbers in a single group instead of splitting
    by game rules (e.g. dlt returns 7 numbers in one group instead of
    front=5 + back=2). This function splits them correctly.
    """
    rule = GAME_RULES[game_code]
    expected_groups = len(rule["groups"])
    expected_picks = [g["pick"] for g in rule["groups"]]
    total_expected = sum(expected_picks)

    if len(groups_data) == expected_groups:
        # Already correctly split — just return as-is
        return groups_data

    if len(groups_data) == 1:
        # All numbers merged into one group — split by game rules
        all_nums = groups_data[0].get("numbers", [])
        if len(all_nums) >= total_expected:
            split_groups = []
            offset = 0
            for gi, g_rule in enumerate(rule["groups"]):
                pick = g_rule["pick"]
                nums = all_nums[offset:offset + pick]
                split_groups.append({"name": g_rule["name"], "numbers": nums})
                offset += pick
            return split_groups

    # For digit-by-digit games (3d/pl5) with mismatched groups,
    # try to flatten all numbers and redistribute
    if game_code in ("3d", "pl5"):
        all_nums = []
        for g in groups_data:
            all_nums.extend(g.get("numbers", []))
        if len(all_nums) >= total_expected:
            split_groups = []
            offset = 0
            for gi, g_rule in enumerate(rule["groups"]):
                pick = g_rule["pick"]
                nums = all_nums[offset:offset + pick]
                split_groups.append({"name": g_rule["name"], "numbers": nums})
                offset += pick
            return split_groups

    # Return as-is if we can't normalize
    return groups_data


def _parse_llm_response(text: str, game_code: str) -> List[Candidate]:
    """Parse the LLM JSON response into Candidate objects."""
    rule = GAME_RULES[game_code]
    game_name = rule["name"]

    # Try to extract JSON from the response (LLM may add extra text)
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if not json_match:
        raise ValueError(f"无法从LLM响应中提取JSON: {text[:200]}")

    data = json.loads(json_match.group())
    candidates_data = data.get("candidates", [])
    if not candidates_data:
        raise ValueError(f"LLM响应中无candidates: {text[:200]}")

    candidates: List[Candidate] = []
    for idx, item in enumerate(candidates_data):
        groups = item.get("groups", [])

        # Normalize groups to match expected game structure
        groups = _normalize_groups(groups, game_code)

        numbers_parts = []
        reason = item.get("reason", "LLM推荐")
        for g_data in groups:
            nums = g_data.get("numbers", [])
            numbers_parts.append(tuple(nums))

        # Build number_text based on game type
        number_text = _build_number_text(numbers_parts, game_code)
        pick = _build_pick(numbers_parts, game_code)

        candidates.append(Candidate(
            rank=idx + 1,
            strategy_name=f"{game_name}AI智能",
            numbers=pick,
            number_text=number_text,
            reason=reason,
        ))

    return candidates


def _build_number_text(numbers_parts: list, game_code: str) -> str:
    """Build display text from parsed number groups."""
    rule = GAME_RULES[game_code]
    if game_code in ("3d", "pl5"):
        # Digit-by-digit games: concatenate
        digits = []
        for part in numbers_parts:
            digits.extend(str(n) for n in part)
        return "".join(digits)
    if game_code == "qlc":
        return "".join(str(n) for n in sorted(numbers_parts[0]))
    if game_code == "kl8":
        return " ".join(str(n) for n in sorted(numbers_parts[0]))
    if game_code == "ssq":
        red = " ".join(str(n) for n in sorted(numbers_parts[0]))
        blue = str(numbers_parts[1][0]) if len(numbers_parts) > 1 else "1"
        return f"红球({red}) 蓝球({blue})"
    if game_code == "dlt":
        front = " ".join(str(n) for n in sorted(numbers_parts[0]))
        back = " ".join(str(n) for n in sorted(numbers_parts[1]))
        return f"前区({front}) 后区({back})"
    return str(numbers_parts)


def _build_pick(numbers_parts: list, game_code: str) -> Any:
    """Build the game-specific pick object from parsed numbers."""
    if game_code == "3d":
        return tuple(numbers_parts[i][0] for i in range(min(3, len(numbers_parts))))
    if game_code == "pl5":
        return tuple(numbers_parts[i][0] for i in range(min(5, len(numbers_parts))))
    if game_code == "qlc":
        from lottery_sim.models import QlcPick
        return QlcPick(numbers=tuple(sorted(numbers_parts[0])))
    if game_code == "kl8":
        from lottery_sim.models import Kl8Pick
        return Kl8Pick(numbers=tuple(sorted(numbers_parts[0])))
    if game_code == "ssq":
        from lottery_sim.models import SsqPick
        red = tuple(sorted(numbers_parts[0]))
        blue = numbers_parts[1][0] if len(numbers_parts) > 1 else 1
        return SsqPick(red=red, blue=blue)
    if game_code == "dlt":
        from lottery_sim.models import DltPick
        front = tuple(sorted(numbers_parts[0]))
        back = tuple(sorted(numbers_parts[1]))
        return DltPick(front=front, back=back)
    return numbers_parts


def _call_llm_api(
    prompt: str,
    base_url: str,
    model: str,
    api_key: str,
    max_tokens: int = 4096,
    timeout: float = 120.0,
) -> str:
    """Make a single LLM API call and return the content string."""
    api_url = base_url.rstrip("/")
    if not api_url.endswith("/v1"):
        api_url += "/v1"
    api_url += "/chat/completions"

    response = httpx.post(
        api_url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.8,
            "max_tokens": max_tokens,
        },
        timeout=timeout,
    )

    if response.status_code != 200:
        raise ValueError(f"LLM API返回错误: HTTP {response.status_code}, {response.text[:300]}")

    result = response.json()
    content = result["choices"][0]["message"]["content"]
    finish_reason = result["choices"][0].get("finish_reason", "unknown")

    if finish_reason == "length" or not content:
        raise ValueError(f"LLM响应被截断(finish_reason={finish_reason})或内容为空")

    return content


def llm_recommend(
    draws: Sequence[Any],
    game_code: str,
    game_name: str,
    count: int = 10,
    adapter: Any = None,
) -> List[Candidate]:
    """Call LLM API to recommend lottery numbers.

    Uses batched calls (max 3 candidates per call) to avoid API truncation.
    Returns list of Candidate objects. Raises on API/parsing failure
    so the caller can fall back to ML model.
    """
    base_url, model, api_key = _llm_config_from_env()
    if not base_url or not api_key:
        raise ValueError("LLM配置不完整：缺少base_url或api_key")

    all_candidates: List[Candidate] = []
    remaining = count
    batch_num = 0

    while remaining > 0:
        batch_size = min(remaining, _MAX_BATCH)
        batch_num += 1

        prompt = _build_prompt(draws, game_code, batch_size)
        content = _call_llm_api(prompt, base_url, model, api_key, max_tokens=4096)
        candidates = _parse_llm_response(content, game_code)

        all_candidates.extend(candidates)
        remaining -= len(candidates)

        # If we got fewer candidates than requested, stop retrying
        if len(candidates) < batch_size:
            break

    # Re-rank all candidates
    for i, c in enumerate(all_candidates):
        all_candidates[i] = Candidate(
            rank=i + 1,
            strategy_name=c.strategy_name,
            numbers=c.numbers,
            number_text=c.number_text,
            reason=c.reason,
        )

    # Limit to requested count
    if len(all_candidates) > count:
        all_candidates = all_candidates[:count]

    return all_candidates
