"""Trade statistics. Empty samples and one-sided samples stay explicit."""

from __future__ import annotations

import math
from typing import Literal

from oppfinder.config import EQUITY0, MIN_SAMPLE

EvidenceLabel = Literal[
    "too_small",
    "undefined",
    "positive_point_estimate_no_variance",
    "negative_point_estimate_no_variance",
    "positive_interval_above_zero",
    "negative_interval_below_zero",
    "positive_interval_includes_zero",
    "negative_interval_includes_zero",
    "flat",
]


def _never(value: EvidenceLabel) -> None:
    raise AssertionError(f"unhandled evidence label: {value}")


def mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def expectancy(pnls: list[float]) -> float | None:
    """Mean P&L per trade, including scratches as zeros."""
    return mean(pnls)


def win_rate(pnls: list[float]) -> float | None:
    if not pnls:
        return None
    return sum(1 for value in pnls if value > 0) / len(pnls)


def average_win(pnls: list[float]) -> float | None:
    wins = [value for value in pnls if value > 0]
    return mean(wins)


def average_loss(pnls: list[float]) -> float | None:
    losses = [value for value in pnls if value < 0]
    return mean(losses)


def profit_factor(pnls: list[float]) -> float | None:
    """Gross wins divided by absolute gross losses. None when there is no loss."""
    gains = sum(value for value in pnls if value > 0)
    losses = sum(value for value in pnls if value < 0)
    if losses == 0:
        return None
    return gains / abs(losses)


def max_drawdown(equity: list[float]) -> float:
    """Largest peak-to-trough decline as a fraction of the peak."""
    if not equity:
        raise ValueError("equity curve is empty")
    peak = equity[0]
    worst = 0.0
    for value in equity:
        if value > peak:
            peak = value
        if peak > 0:
            worst = max(worst, (peak - value) / peak)
        elif value < 0:
            worst = max(worst, 1.0)
    return worst


def equity_curve(pnls_in_exit_order: list[float], start: float = EQUITY0) -> list[float]:
    curve = [start]
    total = start
    for pnl in pnls_in_exit_order:
        total += pnl
        curve.append(total)
    return curve


def t_stat(values: list[float]) -> float | None:
    n = len(values)
    if n < 2:
        return None
    center = sum(values) / n
    var = sum((value - center) ** 2 for value in values) / (n - 1)
    if var <= 0:
        return None
    return center / math.sqrt(var / n)


def normal_two_sided_p(stat: float) -> float:
    """Two-sided p-value using a normal approximation of the t statistic."""
    return math.erfc(abs(stat) / math.sqrt(2))


def confidence_interval(values: list[float]) -> tuple[float, float] | None:
    """Normal 1.96-SE interval. None when the sample has fewer than 2 points or no variance."""
    n = len(values)
    if n < 2:
        return None
    center = sum(values) / n
    var = sum((value - center) ** 2 for value in values) / (n - 1)
    if var <= 0:
        return None
    se = math.sqrt(var / n)
    return center - 1.96 * se, center + 1.96 * se


def evidence_label(n: int, mean_r: float | None, ci: tuple[float, float] | None) -> EvidenceLabel:
    if n < MIN_SAMPLE:
        return "too_small"
    if mean_r is None:
        return "undefined"
    if ci is None:
        if mean_r > 0:
            return "positive_point_estimate_no_variance"
        if mean_r < 0:
            return "negative_point_estimate_no_variance"
        return "flat"
    low, high = ci
    if mean_r > 0 and low > 0:
        return "positive_interval_above_zero"
    if mean_r < 0 and high < 0:
        return "negative_interval_below_zero"
    if mean_r > 0:
        return "positive_interval_includes_zero"
    if mean_r < 0:
        return "negative_interval_includes_zero"
    return "flat"


def evidence_sentence(label: EvidenceLabel, n: int) -> str:
    if label == "too_small":
        return (
            f"Sample is {n} closed trades, below {MIN_SAMPLE}. "
            "The point estimate is descriptive only and is not evidence of a repeatable edge."
        )
    if label == "undefined":
        return "Mean R is undefined for this sample."
    if label == "positive_point_estimate_no_variance":
        return (
            f"All {n} closed trades had the same positive R, so there is no variance to test. "
            "That is not treated as a confirmed edge."
        )
    if label == "negative_point_estimate_no_variance":
        return f"All {n} closed trades had the same negative R."
    if label == "positive_interval_above_zero":
        return (
            f"n={n}. Mean R is positive and a normal 95% interval is above zero. "
            "Trades overlap in time and the names are highly correlated, so the effective "
            "sample is smaller than n. Treat this as the strongest evidence in the test, not as proof."
        )
    if label == "negative_interval_below_zero":
        return (
            f"n={n}. Mean R is negative and a normal 95% interval is below zero, "
            "with the same correlation caveat."
        )
    if label == "positive_interval_includes_zero":
        return (
            f"n={n}. The average R is positive in this sample, but the normal 95% interval "
            "includes zero. That is not enough to call the approach a winner."
        )
    if label == "negative_interval_includes_zero":
        return (
            f"n={n}. The average R is negative in this sample, but the normal 95% interval "
            "includes zero."
        )
    if label == "flat":
        return f"n={n}. Mean R is zero."
    _never(label)
    return ""


def pearson(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n != len(ys) or n < 3:
        return None
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    dy = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return None
    return num / (dx * dy)


def max_concurrent_risk(trades: list[dict]) -> float:
    """Peak sum of open defined-risk dollars. Same-day exits release before new entries."""
    events: list[tuple[object, int, float]] = []
    for trade in trades:
        risk = float(trade.get("risk_dollars") or 0.0)
        entry = trade.get("entry_date")
        exit_date = trade.get("exit_date")
        if entry is None or exit_date is None:
            continue
        events.append((entry, 1, risk))
        events.append((exit_date, -1, risk))
    events.sort(key=lambda item: (str(item[0]), item[1]))
    running = 0.0
    peak = 0.0
    for _, sign, risk in events:
        running += sign * risk
        peak = max(peak, running)
    return peak


def summarize_core(trades: list[dict]) -> dict:
    """Summarize closed trades only. `trades` must already be the closed subset."""
    ordered = sorted(trades, key=lambda trade: (str(trade.get("exit_date")), str(trade.get("symbol"))))
    pnls = [float(trade["pnl"]) for trade in ordered]
    rs = [float(trade["r_multiple"]) for trade in ordered]
    n = len(ordered)
    center_r = mean(rs)
    ci = confidence_interval(rs) if n else None
    label = evidence_label(n, center_r, ci)
    t_value = t_stat(rs) if n else None
    curve = equity_curve(pnls) if n else [EQUITY0]
    return {
        "n": n,
        "win_rate": win_rate(pnls),
        "avg_win": average_win(pnls),
        "avg_loss": average_loss(pnls),
        "expectancy": expectancy(pnls),
        "profit_factor": profit_factor(pnls),
        "max_drawdown": max_drawdown(curve) if n else None,
        "sum_pnl": sum(pnls) if n else 0.0,
        "mean_r": center_r,
        "median_r": _median(rs),
        "t_stat": t_value,
        "p_value_normal": None if t_value is None or n < MIN_SAMPLE else normal_two_sided_p(t_value),
        "ci95_low": None if ci is None else ci[0],
        "ci95_high": None if ci is None else ci[1],
        "evidence": label,
        "note": evidence_sentence(label, n),
        "max_concurrent_risk": max_concurrent_risk(ordered) if n else 0.0,
        "ending_equity": curve[-1],
    }


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def summarize(trades: list[dict]) -> dict:
    closed = [trade for trade in trades if trade.get("status") == "closed"]
    core = summarize_core(closed)
    core["by_trend"] = _slices(closed, "trend_regime", ("uptrend", "downtrend", "range", "unknown"))
    core["by_vol"] = _slices(closed, "vol_regime", ("high_vol", "low_vol", "unknown"))
    return core


def _slices(trades: list[dict], field: str, keys: tuple[str, ...]) -> dict:
    return {key: summarize_core([trade for trade in trades if trade.get(field) == key]) for key in keys}


def _score(row: dict, field: str) -> float:
    value = row.get(field)
    if value is None:
        return -1e9
    return float(value)


def select_headline(rows: list[dict], result_type: str = "direct_option") -> dict:
    """Pick the result a report is allowed to lead with.

    A strategy is supported only when n >= 30 and the normal interval for mean R
    is entirely above zero. A positive average whose interval includes zero is a
    point estimate, not a winner.
    """
    chosen = [row for row in rows if row.get("result_type") == result_type]
    strong = [row for row in chosen if row.get("evidence") == "positive_interval_above_zero"]
    if strong:
        best = max(strong, key=lambda row: _score(row, "ci95_low"))
        return {"status": "supported", "row": best}
    positive = [
        row
        for row in chosen
        if row.get("evidence") == "positive_interval_includes_zero" and int(row.get("n") or 0) >= MIN_SAMPLE
    ]
    if positive:
        best = max(positive, key=lambda row: _score(row, "mean_r"))
        return {"status": "positive_not_significant", "row": best}
    if not chosen:
        return {"status": "no_trades", "row": None}
    adequate = [row for row in chosen if int(row.get("n") or 0) >= MIN_SAMPLE]
    if not adequate:
        return {"status": "all_samples_too_small", "row": None}
    least_bad = max(adequate, key=lambda row: _score(row, "mean_r"))
    return {"status": "no_positive_edge", "row": least_bad}
