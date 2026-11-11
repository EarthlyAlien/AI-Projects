"""Underlying proxy: next-open fills, a hard ATR stop, and fixed fractional risk.

The P&L is the stock's, with a stop. It is not an option fill. Callers label it
`underlying_proxy`.
"""

from __future__ import annotations

import math
from datetime import date
from typing import Callable

from oppfinder.config import ATR_STOP_MULT, EQUITY0, RISK_FRAC, STOCK_SLIPPAGE_BPS


def apply_slippage(price: float, side: int, action: str) -> float:
    """Adverse  slippage. `side` is +1 for a long position and -1 for a short."""
    if side not in (1, -1):
        raise ValueError(side)
    if action not in ("entry", "exit"):
        raise ValueError(action)
    bps = STOCK_SLIPPAGE_BPS / 10_000
    if action == "entry":
        return price * (1 + side * bps)
    return price * (1 - side * bps)


def _stop_hit(side: int, bar: dict, stop_level: float) -> str | None:
    open_ = float(bar["open"])
    if side == 1:
        if open_ <= stop_level:
            return "gap"
        if float(bar["low"]) <= stop_level:
            return "intra"
        return None
    if side == -1:
        if open_ >= stop_level:
            return "gap"
        if float(bar["high"]) >= stop_level:
            return "intra"
        return None
    raise ValueError(side)


def _closed(records: list[dict], index: int, side: int, reason: str, raw_price: float) -> dict:
    return {
        "status": "closed",
        "exit_index": index,
        "exit_reason": reason,
        "exit_price": apply_slippage(raw_price, side, "exit"),
        "exit_date": records[index]["date"],
    }


def _walk_exit(
    records: list[dict],
    entry_index: int,
    side: int,
    stop_level: float,
    max_hold: int,
    invalidated: Callable[[dict, int, float | None], bool],
    level: float | None,
) -> dict:
    time_exit = entry_index + max_hold
    scheduled_index: int | None = None
    scheduled_reason: str | None = None
    last = len(records) - 1
    for index in range(entry_index, len(records)):
        if scheduled_index is not None and index == scheduled_index:
            return _closed(records, index, side, scheduled_reason or "invalidation", float(records[index]["open"]))
        if index == time_exit:
            return _closed(records, index, side, "time", float(records[index]["open"]))
        hit = _stop_hit(side, records[index], stop_level)
        if hit == "gap":
            return _closed(records, index, side, "gap_stop", float(records[index]["open"]))
        if hit == "intra":
            return _closed(records, index, side, "stop", stop_level)
        if index + 1 <= last and invalidated(records[index], side, level):
            scheduled_index = index + 1
            scheduled_reason = "invalidation"
    mark = apply_slippage(float(records[last]["close"]), side, "exit")
    return {
        "status": "open",
        "exit_index": last,
        "exit_reason": "open",
        "exit_price": mark,
        "exit_date": records[last]["date"],
    }


def run_protected_trades(
    records: list[dict],
    *,
    symbol: str,
    strategy: str,
    side_at: Callable[[list[dict], int], int],
    max_hold: int,
    invalidated: Callable[[dict, int, float | None], bool],
    level_at: Callable[[list[dict], int, int], float | None],
    study_start: date,
    study_end: date,
) -> tuple[list[dict], list[dict]]:
    if max_hold < 1:
        raise ValueError("max_hold must be at least 1")
    trades: list[dict] = []
    skips: list[dict] = []
    index = 0
    while index < len(records) - 1:
        signal_date = records[index]["date"]
        side = side_at(records, index)
        if side == 0 or signal_date < study_start or signal_date > study_end:
            index += 1
            continue
        entry_index = index + 1
        atr = records[index].get("atr14")
        entry_open = records[entry_index].get("open")
        if atr is None or float(atr) <= 0 or entry_open is None:
            skips.append(_skip(symbol, strategy, signal_date, "missing_atr_or_open"))
            index += 1
            continue
        entry_open_f = float(entry_open)
        stop_level = entry_open_f - side * ATR_STOP_MULT * float(atr)
        entry_fill = apply_slippage(entry_open_f, side, "entry")
        stop_model = apply_slippage(stop_level, side, "exit")
        risk_per_share = side * (entry_fill - stop_model)
        if risk_per_share <= 0:
            skips.append(_skip(symbol, strategy, signal_date, "nonpositive_risk"))
            index += 1
            continue
        shares = int(math.floor((EQUITY0 * RISK_FRAC) / risk_per_share))
        if shares < 1:
            skips.append(_skip(symbol, strategy, signal_date, "risk_budget"))
            index += 1
            continue
        level = level_at(records, index, side)
        walked = _walk_exit(records, entry_index, side, stop_level, max_hold, invalidated, level)
        exit_fill = float(walked["exit_price"])
        risk_dollars = shares * risk_per_share
        pnl = None
        r_multiple = None
        unrealized = None
        if walked["status"] == "closed":
            pnl = side * (exit_fill - entry_fill) * shares
            r_multiple = pnl / risk_dollars
        else:
            unrealized = side * (exit_fill - entry_fill) * shares
        signal = records[index]
        trades.append(
            {
                "result_type": "underlying_proxy",
                "strategy": strategy,
                "symbol": symbol,
                "side": "long" if side == 1 else "short",
                "side_sign": side,
                "status": walked["status"],
                "signal_date": signal_date,
                "signal_index": index,
                "entry_date": records[entry_index]["date"],
                "entry_index": entry_index,
                "exit_date": walked["exit_date"],
                "exit_index": walked["exit_index"],
                "exit_reason": walked["exit_reason"],
                "entry_open": entry_open_f,
                "entry_price": entry_fill,
                "exit_price": exit_fill,
                "stop_price": stop_level,
                "shares": shares,
                "risk_dollars": risk_dollars,
                "pnl": pnl,
                "unrealized_pnl": unrealized,
                "r_multiple": r_multiple,
                "trend_regime": signal.get("trend_regime") or "unknown",
                "vol_regime": signal.get("vol_regime") or "unknown",
                "entry_iv": signal.get("iv"),
                "entry_rv20": signal.get("rv20"),
                "iv_percentile": signal.get("iv_pct"),
                "level": level,
            }
        )
        if walked["status"] == "closed":
            index = int(walked["exit_index"]) + 1
        else:
            break
    return trades, skips


def _skip(symbol: str, strategy: str, signal_date: date, reason: str) -> dict:
    return {
        "result_type": "underlying_proxy",
        "symbol": symbol,
        "strategy": strategy,
        "signal_date": signal_date,
        "reason": reason,
    }
