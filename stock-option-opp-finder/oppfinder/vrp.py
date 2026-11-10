"""Implied vol versus the realized vol that actually followed.

This is not a fill and it is not a P&L. Windows do not overlap.
"""

from __future__ import annotations

from datetime import date
from typing import Callable

from oppfinder.config import PREMIUM_HOLD, TRADING_DAYS
from oppfinder.indicators import expected_move, forward_realized_vol


def variance_risk_observations(
    records: list[dict],
    *,
    symbol: str,
    source: str,
    study_start: date,
    study_end: date,
    side_at: Callable[[list[dict], int], int],
    horizon: int = PREMIUM_HOLD,
) -> list[dict]:
    closes = [float(row["close"]) for row in records]
    observations: list[dict] = []
    index = 0
    while index < len(records):
        day = records[index]["date"]
        if day < study_start:
            index += 1
            continue
        if day > study_end:
            break
        side = side_at(records, index)
        iv = records[index].get("iv")
        end = index + horizon
        if side == 0 or iv is None or end >= len(records):
            index += 1
            continue
        forward = forward_realized_vol(closes, index, horizon)
        if forward is None:
            index += 1
            continue
        simple = closes[end] / closes[index] - 1
        move = expected_move(float(iv), horizon, TRADING_DAYS)
        adverse = (side == 1 and simple < -move) or (side == -1 and simple > move)
        observations.append(
            {
                "result_type": source,
                "symbol": symbol,
                "signal_date": day,
                "end_date": records[end]["date"],
                "side": "put_credit" if side == 1 else "call_credit",
                "iv": float(iv),
                "forward_rv": forward,
                "iv_minus_rv": float(iv) - forward,
                "variance_gap": float(iv) ** 2 - forward ** 2,
                "underlying_return": simple,
                "expected_move": move,
                "inside_expected_move": abs(simple) < move,
                "adverse_beyond_expected_move": adverse,
                "trend_regime": records[index].get("trend_regime") or "unknown",
                "vol_regime": records[index].get("vol_regime") or "unknown",
                "horizon_sessions": horizon,
            }
        )
        index += horizon
    return observations


def summarize_vrp(rows: list[dict]) -> dict:
    n = len(rows)
    if n == 0:
        return {
            "n": 0,
            "mean_iv": None,
            "mean_forward_rv": None,
            "mean_iv_minus_rv": None,
            "mean_variance_gap": None,
            "fraction_rv_below_iv": None,
            "fraction_inside_expected_move": None,
            "fraction_adverse": None,
            "note": "No non-overlapping windows had both an IV reading and a full forward path.",
        }
    return {
        "n": n,
        "mean_iv": _avg(rows, "iv"),
        "mean_forward_rv": _avg(rows, "forward_rv"),
        "mean_iv_minus_rv": _avg(rows, "iv_minus_rv"),
        "mean_variance_gap": _avg(rows, "variance_gap"),
        "fraction_rv_below_iv": sum(1 for row in rows if row["forward_rv"] < row["iv"]) / n,
        "fraction_inside_expected_move": sum(1 for row in rows if row["inside_expected_move"]) / n,
        "fraction_adverse": sum(1 for row in rows if row["adverse_beyond_expected_move"]) / n,
        "note": (
            f"{n} non-overlapping {rows[0]['horizon_sessions']}-session windows. "
            "This compares a volatility reading with the realized volatility that followed. "
            "It is not a spread P&L, and the vendor IV tenor is not documented in the source table, "
            "so a positive gap is a sign check rather than a matched-tenor variance swap."
        ),
    }


def _avg(rows: list[dict], key: str) -> float:
    return sum(float(row[key]) for row in rows) / len(rows)
