"""Close-to-close drift after a signal. This is not a filled trade."""

from __future__ import annotations

import math
import statistics
from datetime import date
from typing import Callable

from oppfinder.stats import confidence_interval, evidence_label, evidence_sentence, mean, pearson, win_rate

SideFn = Callable[[list[dict], int], int]


def signal_windows(
    records: list[dict],
    side_at: SideFn,
    horizon: int,
    study_start: date,
    study_end: date,
    *,
    overlap: str,
) -> list[dict]:
    """Signed close-to-close return from the signal close to the close `horizon` sessions later.

    `overlap="overlapping"` keeps every signal whose forward window fits.
    `overlap="non_overlapping"` starts the next search on the window's last bar,
    so adjacent windows share a boundary close and no interior sessions.
    A window that runs off the sample is omitted. No price is invented.
    """
    if overlap not in ("overlapping", "non_overlapping"):
        raise ValueError(overlap)
    if horizon < 1:
        raise ValueError("horizon must be at least 1")
    if overlap == "overlapping":
        indexes = range(len(records))
        return [row for index in indexes if (row := _window(records, index, side_at, horizon, study_start, study_end, overlap))]
    rows: list[dict] = []
    index = 0
    while index < len(records):
        row = _window(records, index, side_at, horizon, study_start, study_end, overlap)
        if row is None:
            index += 1
            continue
        rows.append(row)
        index = int(row["end_index"])
    return rows


def summarize_windows(rows: list[dict]) -> dict:
    signed = [float(row["signed_return"]) for row in rows]
    n = len(signed)
    center = mean(signed)
    ci = confidence_interval(signed) if n else None
    label = evidence_label(n, center, ci)
    return {
        "n": n,
        "mean_signed_return": center,
        "win_rate": win_rate(signed),
        "ci95_low": None if ci is None else ci[0],
        "ci95_high": None if ci is None else ci[1],
        "evidence": label,
        "note": evidence_sentence(label, n),
    }


def path_summary(records: list[dict], study_start: date, study_end: date) -> dict:
    """Buy-and-hold facts for one price path. One path is not a strategy sample."""
    study = [row for row in records if study_start <= row["date"] <= study_end]
    if len(study) < 2:
        return {
            "sessions": len(study),
            "start_date": study[0]["date"].isoformat() if study else None,
            "end_date": study[-1]["date"].isoformat() if study else None,
            "start_close": study[0]["close"] if study else None,
            "end_close": study[-1]["close"] if study else None,
            "simple_return": None,
            "max_drawdown": None,
            "realized_vol": None,
            "avg_share_volume": None,
            "avg_dollar_volume": None,
        }
    closes = [float(row["close"]) for row in study]
    simple = closes[-1] / closes[0] - 1 if closes[0] else None
    logs = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes)) if closes[i - 1] > 0 and closes[i] > 0]
    realized = statistics.stdev(logs) * math.sqrt(252) if len(logs) >= 2 else None
    volumes = [float(row["volume"]) for row in study if row.get("volume") is not None]
    dollars = [
        float(row["close"]) * float(row["volume"])
        for row in study
        if row.get("volume") is not None and row.get("close") is not None
    ]
    return {
        "sessions": len(study),
        "start_date": study[0]["date"].isoformat(),
        "end_date": study[-1]["date"].isoformat(),
        "start_close": closes[0],
        "end_close": closes[-1],
        "simple_return": simple,
        "max_drawdown": _close_drawdown(closes),
        "realized_vol": realized,
        "avg_share_volume": mean(volumes),
        "avg_dollar_volume": mean(dollars),
    }


def linked_returns(left: list[dict], right: list[dict], study_start: date, study_end: date) -> dict:
    """Daily simple-return correlation and beta of `right` on `left` over shared sessions."""
    left_map = _daily_returns(left, study_start, study_end)
    right_map = _daily_returns(right, study_start, study_end)
    shared = sorted(set(left_map) & set(right_map))
    xs = [left_map[day] for day in shared]
    ys = [right_map[day] for day in shared]
    var_x = _variance(xs)
    beta = None
    if var_x:
        cov = sum((x - (sum(xs) / len(xs))) * (y - (sum(ys) / len(ys))) for x, y in zip(xs, ys)) / (len(xs) - 1)
        beta = cov / var_x
    return {"n": len(shared), "correlation": pearson(xs, ys), "beta": beta}


def _window(records, index, side_at, horizon, study_start, study_end, overlap):
    bar = records[index]
    signal_date = bar["date"]
    if signal_date < study_start or signal_date > study_end:
        return None
    side = side_at(records, index)
    if side == 0:
        return None
    end = index + horizon
    if end >= len(records):
        return None
    start_close = float(bar["close"])
    end_close = float(records[end]["close"])
    if start_close == 0:
        return None
    raw = end_close / start_close - 1
    return {
        "overlap": overlap,
        "signal_date": signal_date,
        "end_date": records[end]["date"],
        "signal_index": index,
        "end_index": end,
        "side": side,
        "raw_return": raw,
        "signed_return": side * raw,
        "trend_regime": bar.get("trend_regime") or "unknown",
        "vol_regime": bar.get("vol_regime") or "unknown",
    }


def _daily_returns(records: list[dict], study_start: date, study_end: date) -> dict[date, float]:
    out: dict[date, float] = {}
    for index in range(1, len(records)):
        day = records[index]["date"]
        if day < study_start or day > study_end:
            continue
        prev = float(records[index - 1]["close"])
        close = float(records[index]["close"])
        if prev == 0:
            continue
        out[day] = close / prev - 1
    return out


def _variance(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    center = sum(values) / len(values)
    var = sum((value - center) ** 2 for value in values) / (len(values) - 1)
    if var <= 0:
        return None
    return var


def _close_drawdown(closes: list[float]) -> float:
    peak = closes[0]
    worst = 0.0
    for price in closes:
        if price > peak:
            peak = price
        if peak > 0:
            worst = max(worst, (peak - price) / peak)
    return worst
