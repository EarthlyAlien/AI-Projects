"""One- and two-session defined-risk credit verticals, marked at the next end-of-day chains.

The historical chain is a sampled grid, so an exit strike that is missing stays
missing. A one-day trade whose exit legs are absent is unmarked, not modeled.
"""

from __future__ import annotations

import math
import statistics
from datetime import date
from decimal import Decimal
from typing import Callable

from oppfinder.options_backtest import ChainGetter, _split_between, _spot
from oppfinder.signals import mean_reversion_side, premium_side, trend_side
from oppfinder.spreads import Spread, build_credit_vertical, find_leg, option_pnl, size_contracts, spot_matches
from oppfinder.stats import mean, win_rate

NEAR_DTE = (14, 5, 25)
MONTHLY_DTE = (35, 25, 55)

SideFn = Callable[[list[dict], int], int]

FAMILIES: dict[str, SideFn] = {
    "high_iv": premium_side,
    "mr_fade": mean_reversion_side,
    "trend_aligned": trend_side,
}

# (label, sessions held, take profit at half the credit on the first mark)
EXITS: tuple[tuple[str, int, bool], ...] = (
    ("hold1", 1, False),
    ("hold2", 2, False),
    ("pt50_by_day2", 2, True),
)


def backtest_short_credit(
    records: list[dict],
    symbol: str,
    family: str,
    hold: int,
    profit_target: bool,
    dte: tuple[int, int, int],
    chain_getter: ChainGetter,
    splits: list[date],
    study_start: date,
    study_end: date,
    *,
    side_at: SideFn | None = None,
) -> tuple[list[dict], list[dict], list[dict]]:
    """Sell a one-strike credit vertical on the session after the signal.

    Bullish signal sells a put vertical, bearish sells a call vertical. The exit
    is the end-of-day chain exactly `hold` sessions after entry. With
    `profit_target`, the first session's closing debit is checked: at or below
    half the credit received, the trade closes there, otherwise it closes on
    the second session. No forward search is used, because searching later
    chains would change the holding period being tested.
    """
    if hold < 1:
        raise ValueError("hold must be at least 1")
    side_fn = side_at or FAMILIES[family]
    variant = f"{family}_{'pt50_by_day2' if profit_target else f'hold{hold}'}"
    trades: list[dict] = []
    skips: list[dict] = []
    unmarked: list[dict] = []
    index = 0
    while index < len(records) - 1:
        signal_date = records[index]["date"]
        side = side_fn(records, index)
        if side == 0 or signal_date < study_start or signal_date > study_end:
            index += 1
            continue
        entry_i = index + 1
        exit_i = entry_i + hold
        if exit_i >= len(records):
            skips.append(_row(symbol, variant, signal_date, "open_at_sample_end"))
            break
        if _split_between(splits, records[entry_i]["date"], records[exit_i]["date"]):
            skips.append(_row(symbol, variant, signal_date, "split_between"))
            index = exit_i + 1
            continue
        right = "PUT" if side == 1 else "CALL"
        status, rows = chain_getter(symbol, records[entry_i]["date"])
        if status != "ok":
            skips.append(_row(symbol, variant, signal_date, f"entry_chain_{status}"))
            index += 1
            continue
        spread, reason = build_credit_vertical(rows, _spot(records[entry_i]), records[entry_i]["date"], right, dte)
        if spread is None:
            skips.append(_row(symbol, variant, signal_date, reason))
            index += 1
            continue
        if not spot_matches(rows, _spot(records[entry_i]), spread.expiration):
            skips.append(_row(symbol, variant, signal_date, "spot_chain_mismatch"))
            index += 1
            continue
        spot_now = float(records[entry_i]["raw_close"])
        if (side == 1 and spot_now < float(spread.short_strike)) or (
            side == -1 and spot_now > float(spread.short_strike)
        ):
            skips.append(_row(symbol, variant, signal_date, "already_through_strike"))
            index += 1
            continue
        contracts = size_contracts(spread.max_loss)
        if contracts is None:
            skips.append(_row(symbol, variant, signal_date, "risk_budget"))
            index = exit_i + 1
            continue
        exit_at, exit_reason, legs = _exit_marks(
            records, symbol, entry_i, exit_i, spread, chain_getter, profit_target
        )
        base = {
            "result_type": "direct_option_short",
            "strategy": variant,
            "family": family,
            "symbol": symbol,
            "side": "long" if side == 1 else "short",
            "side_sign": side,
            "signal_date": signal_date,
            "entry_date": records[entry_i]["date"],
            "expiration": spread.expiration,
            "long_strike": spread.long_strike,
            "short_strike": spread.short_strike,
            "premium": spread.premium,
            "width": spread.width,
        }
        if legs is None or exit_at is None:
            unmarked.append(
                {
                    **base,
                    "status": "unmarked",
                    "intended_exit": records[exit_i]["date"],
                    "reason": "exit_quote_missing",
                    "underlying_return": records[exit_i]["close"] / records[entry_i]["close"] - 1,
                }
            )
            index = exit_i + 1
            continue
        long_leg, short_leg = legs
        pnl, commission = option_pnl(spread, long_leg.bid, short_leg.ask, contracts)
        defined = spread.max_loss * Decimal(100) * contracts
        pnl_f = float(pnl)
        trades.append(
            {
                **base,
                "status": "closed",
                "exit_date": records[exit_at]["date"],
                "exit_reason": exit_reason,
                "structure": "credit_" + right.lower(),
                "contracts": contracts,
                "max_loss": spread.max_loss,
                "risk_dollars": float(defined),
                "pnl": pnl_f,
                "r_multiple": pnl_f / float(defined),
                "commissions": float(commission),
                "trend_regime": records[index].get("trend_regime") or "unknown",
                "vol_regime": records[index].get("vol_regime") or "unknown",
                "entry_iv": records[index].get("iv"),
                "entry_rv20": records[index].get("rv20"),
                "iv_percentile": records[index].get("iv_pct"),
                "underlying_return": records[exit_at]["close"] / records[entry_i]["close"] - 1,
            }
        )
        index = exit_i + 1
    return trades, skips, unmarked


def _exit_marks(records, symbol, entry_i, exit_i, spread: Spread, chain_getter, profit_target: bool):
    first_i = entry_i + 1
    if profit_target and first_i < exit_i:
        legs = _legs_on(records, symbol, first_i, spread, chain_getter)
        if legs is None:
            return None, "exit_quote_missing", None
        long_leg, short_leg = legs
        closing_debit = short_leg.ask - long_leg.bid
        if closing_debit <= spread.premium / 2:
            return first_i, "profit_target", legs
    legs = _legs_on(records, symbol, exit_i, spread, chain_getter)
    if legs is None:
        return None, "exit_quote_missing", None
    return exit_i, "time", legs


def _legs_on(records, symbol, at_i, spread: Spread, chain_getter):
    status, rows = chain_getter(symbol, records[at_i]["date"])
    if status != "ok":
        return None
    long_leg = find_leg(rows, spread.expiration, spread.long_strike, spread.right)
    short_leg = find_leg(rows, spread.expiration, spread.short_strike, spread.right)
    if long_leg is None or short_leg is None:
        return None
    return long_leg, short_leg


def premium_windows(
    records: list[dict],
    symbol: str,
    family: str,
    horizon: int,
    study_start: date,
    study_end: date,
    *,
    side_at: SideFn | None = None,
) -> list[dict]:
    """What the underlying did in the sessions after a premium-selling signal.

    Overlapping windows. `adverse_close` is the worst close against the credit
    side, `adverse_intra` the worst high or low. Breach fractions compare that
    adverse move with the expected move implied at the signal close (vendor IV
    when the record has one, otherwise 20-day realized vol). This is a risk
    proxy for a short vertical. It is not an option fill.
    """
    if horizon < 1:
        raise ValueError("horizon must be at least 1")
    side_fn = side_at or FAMILIES[family]
    rows: list[dict] = []
    for index, bar in enumerate(records):
        signal_date = bar["date"]
        if signal_date < study_start or signal_date > study_end:
            continue
        side = side_fn(records, index)
        if side == 0:
            continue
        end = index + horizon
        if end >= len(records):
            continue
        start_close = float(bar["close"])
        if start_close == 0:
            continue
        path = records[index + 1 : end + 1]
        closes = [float(item["close"]) for item in path]
        if side == 1:
            adverse_close = max(0.0, 1 - min(closes) / start_close)
            adverse_intra = max(0.0, 1 - min(float(item["low"]) for item in path) / start_close)
        else:
            adverse_close = max(0.0, max(closes) / start_close - 1)
            adverse_intra = max(0.0, max(float(item["high"]) for item in path) / start_close - 1)
        raw = closes[-1] / start_close - 1
        iv = bar.get("iv")
        rv = bar.get("rv20")
        em_iv = float(iv) * math.sqrt(horizon / 252) if iv is not None else None
        em_rv = float(rv) * math.sqrt(horizon / 252) if rv is not None else None
        em = em_iv if em_iv is not None else em_rv
        logs = [
            math.log(float(path[k]["close"]) / float(path[k - 1]["close"] if k else bar["close"]))
            for k in range(len(path))
        ]
        forward_rv = math.sqrt(sum(value * value for value in logs) / len(logs)) * math.sqrt(252)
        rows.append(
            {
                "symbol": symbol,
                "family": family,
                "horizon": horizon,
                "signal_date": signal_date,
                "end_date": records[end]["date"],
                "side": side,
                "raw_return": raw,
                "signed_return": side * raw,
                "adverse_close": adverse_close,
                "adverse_intra": adverse_intra,
                "expected_move": em,
                "expected_move_source": "vendor_iv" if em_iv is not None else ("rv20" if em_rv is not None else None),
                "breach_close": None if em is None else adverse_close > em,
                "breach_intra": None if em is None else adverse_intra > em,
                "inside_close": None if em is None else abs(raw) <= em,
                "iv": None if iv is None else float(iv),
                "forward_rv": forward_rv,
                "iv_minus_forward_rv": None if iv is None else float(iv) - forward_rv,
            }
        )
    return rows


def summarize_premium_windows(rows: list[dict]) -> dict:
    signed = [float(row["signed_return"]) for row in rows]
    breaches_close = [row["breach_close"] for row in rows if row.get("breach_close") is not None]
    breaches_intra = [row["breach_intra"] for row in rows if row.get("breach_intra") is not None]
    inside = [row["inside_close"] for row in rows if row.get("inside_close") is not None]
    gaps = [float(row["iv_minus_forward_rv"]) for row in rows if row.get("iv_minus_forward_rv") is not None]
    return {
        "n": len(rows),
        "mean_signed_return": mean(signed),
        "median_signed_return": statistics.median(signed) if signed else None,
        "win_rate": win_rate(signed),
        "mean_adverse_close": mean([float(row["adverse_close"]) for row in rows]),
        "mean_adverse_intra": mean([float(row["adverse_intra"]) for row in rows]),
        "breach_close_rate": (sum(1 for value in breaches_close if value) / len(breaches_close)) if breaches_close else None,
        "breach_intra_rate": (sum(1 for value in breaches_intra if value) / len(breaches_intra)) if breaches_intra else None,
        "inside_close_rate": (sum(1 for value in inside if value) / len(inside)) if inside else None,
        "mean_iv_minus_forward_rv": mean(gaps),
        "fraction_forward_rv_below_iv": (
            sum(1 for value in gaps if value > 0) / len(gaps) if gaps else None
        ),
    }


def _row(symbol: str, variant: str, signal_date: date, reason: str) -> dict:
    return {"symbol": symbol, "strategy": variant, "signal_date": signal_date, "reason": reason}
