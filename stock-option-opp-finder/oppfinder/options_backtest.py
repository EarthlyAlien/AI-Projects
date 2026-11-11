"""Listed verticals marked at end-of-day bid/ask. Missing quotes stay missing."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Callable

from oppfinder.config import (
    BREAKOUT_DTE,
    EXIT_QUOTE_FORWARD_SESSIONS,
    MR_DTE,
    PREMIUM_DTE,
    PREMIUM_HOLD,
    TREND_DTE,
)
from oppfinder.signals import BREAKOUT, MEAN_REVERSION, PREMIUM, TREND, premium_side
from oppfinder.spreads import (
    ChainRow,
    Spread,
    atm_gap,
    build_credit_vertical,
    build_debit_vertical,
    find_leg,
    option_pnl,
    size_contracts,
    spot_matches,
)

ChainGetter = Callable[[str, date], tuple[str, list[ChainRow]]]

_DTE = {
    TREND: TREND_DTE,
    MEAN_REVERSION: MR_DTE,
    BREAKOUT: BREAKOUT_DTE,
}


def price_directional(
    symbol: str,
    records: list[dict],
    stock_trades: list[dict],
    splits: list[date],
    chain_getter: ChainGetter,
) -> tuple[list[dict], list[dict], list[dict]]:
    trades: list[dict] = []
    skips: list[dict] = []
    unmarked: list[dict] = []
    dates = [row["date"] for row in records]
    for stock in stock_trades:
        if stock["strategy"] not in _DTE:
            continue
        if stock["status"] != "closed":
            skips.append(_skip(symbol, stock, "underlying_not_closed"))
            continue
        entry_i = int(stock["entry_index"])
        exit_i = int(stock["exit_index"])
        if exit_i <= entry_i:
            skips.append(_skip(symbol, stock, "same_session"))
            continue
        if _split_between(splits, records[entry_i]["date"], records[exit_i]["date"]):
            skips.append(_skip(symbol, stock, "split_between"))
            continue
        right = "CALL" if stock["side_sign"] == 1 else "PUT"
        spread, built, rows, reason = _entry_spread(
            symbol,
            records,
            entry_i,
            chain_getter,
            lambda chain, spot, day: build_debit_vertical(chain, day, right, _DTE[stock["strategy"]]),
        )
        if spread is None:
            skips.append(_skip(symbol, stock, reason))
            continue
        if not spot_matches(rows, _spot(records[entry_i]), spread.expiration):
            skips.append(_skip(symbol, stock, "spot_chain_mismatch", gap=atm_gap(rows, _spot(records[entry_i]), spread.expiration)))
            continue
        contracts = size_contracts(spread.max_loss)
        if contracts is None:
            skips.append(_skip(symbol, stock, "risk_budget"))
            continue
        found = _exit_legs(symbol, dates, records[exit_i]["date"], spread, chain_getter)
        if found is None:
            unmarked.append(_unmarked(symbol, stock, records, entry_i, exit_i, "exit_quote_missing", spread))
            continue
        quote_date, long_leg, short_leg = found
        trades.append(
            _option_trade(
                symbol,
                stock["strategy"],
                stock,
                records,
                entry_i,
                spread,
                contracts,
                long_leg.bid,
                short_leg.ask,
                quote_date,
                "debit_" + right.lower(),
            )
        )
    return trades, skips, unmarked


def price_premium(
    symbol: str,
    records: list[dict],
    splits: list[date],
    chain_getter: ChainGetter,
    study_start: date,
    study_end: date,
    side_at: Callable[[list[dict], int], int] | None = None,
) -> tuple[list[dict], list[dict], list[dict]]:
    trades: list[dict] = []
    skips: list[dict] = []
    unmarked: list[dict] = []
    dates = [row["date"] for row in records]
    side_fn = side_at or premium_side
    index = 0
    while index < len(records) - 1:
        signal_date = records[index]["date"]
        side = side_fn(records, index)
        if side == 0 or signal_date < study_start or signal_date > study_end:
            index += 1
            continue
        entry_i = index + 1
        if _split_between(splits, records[entry_i]["date"], records[min(entry_i + PREMIUM_HOLD, len(records) - 1)]["date"]):
            skips.append(
                {
                    "result_type": "direct_option",
                    "symbol": symbol,
                    "strategy": PREMIUM,
                    "signal_date": signal_date,
                    "reason": "split_between",
                }
            )
            index = entry_i + 1
            continue
        right = "PUT" if side == 1 else "CALL"
        spread, _built_rows_unused, rows, reason = _entry_spread(
            symbol,
            records,
            entry_i,
            chain_getter,
            lambda chain, spot, day: build_credit_vertical(chain, spot, day, right, PREMIUM_DTE),
        )
        if spread is None:
            skips.append(
                {
                    "result_type": "direct_option",
                    "symbol": symbol,
                    "strategy": PREMIUM,
                    "signal_date": signal_date,
                    "reason": reason,
                }
            )
            index += 1
            continue
        if not spot_matches(rows, _spot(records[entry_i]), spread.expiration):
            skips.append(
                {
                    "result_type": "direct_option",
                    "symbol": symbol,
                    "strategy": PREMIUM,
                    "signal_date": signal_date,
                    "reason": "spot_chain_mismatch",
                }
            )
            index += 1
            continue
        spot_now = float(records[entry_i]["raw_close"])
        if (side == 1 and spot_now < float(spread.short_strike)) or (
            side == -1 and spot_now > float(spread.short_strike)
        ):
            skips.append(
                {
                    "result_type": "direct_option",
                    "symbol": symbol,
                    "strategy": PREMIUM,
                    "signal_date": signal_date,
                    "reason": "already_through_strike",
                }
            )
            index += 1
            continue
        exit_i, exit_reason = _premium_exit(records, entry_i, side, float(spread.short_strike))
        if exit_reason == "open" or exit_i is None:
            skips.append(
                {
                    "result_type": "direct_option",
                    "symbol": symbol,
                    "strategy": PREMIUM,
                    "signal_date": signal_date,
                    "reason": "open_at_sample_end",
                }
            )
            break
        if exit_i <= entry_i:
            skips.append(
                {
                    "result_type": "direct_option",
                    "symbol": symbol,
                    "strategy": PREMIUM,
                    "signal_date": signal_date,
                    "reason": "same_session",
                }
            )
            index = exit_i + 1
            continue
        contracts = size_contracts(spread.max_loss)
        if contracts is None:
            skips.append(
                {
                    "result_type": "direct_option",
                    "symbol": symbol,
                    "strategy": PREMIUM,
                    "signal_date": signal_date,
                    "reason": "risk_budget",
                }
            )
            index = exit_i + 1
            continue
        found = _exit_legs(symbol, dates, records[exit_i]["date"], spread, chain_getter)
        stub = {
            "strategy": PREMIUM,
            "side": "long" if side == 1 else "short",
            "side_sign": side,
            "signal_date": signal_date,
            "signal_index": index,
            "entry_date": records[entry_i]["date"],
            "entry_index": entry_i,
            "exit_index": exit_i,
            "exit_reason": exit_reason,
            "trend_regime": records[index].get("trend_regime") or "unknown",
            "vol_regime": records[index].get("vol_regime") or "unknown",
            "entry_iv": records[index].get("iv"),
            "entry_rv20": records[index].get("rv20"),
            "iv_percentile": records[index].get("iv_pct"),
        }
        if found is None:
            unmarked.append(_unmarked(symbol, stub, records, entry_i, exit_i, "exit_quote_missing", spread))
            index = exit_i + 1
            continue
        quote_date, long_leg, short_leg = found
        trades.append(
            _option_trade(
                symbol,
                PREMIUM,
                stub,
                records,
                entry_i,
                spread,
                contracts,
                long_leg.bid,
                short_leg.ask,
                quote_date,
                "credit_" + right.lower(),
            )
        )
        index = exit_i + 1
    return trades, skips, unmarked


def _entry_spread(symbol, records, entry_i, chain_getter, builder):
    entry_date = records[entry_i]["date"]
    status, rows = chain_getter(symbol, entry_date)
    if status != "ok":
        return None, None, rows, f"entry_chain_{status}"
    spot = _spot(records[entry_i])
    spread, reason = builder(rows, spot, entry_date)
    if spread is None:
        return None, rows, rows, reason
    return spread, rows, rows, "ok"


def _premium_exit(records: list[dict], entry_i: int, side: int, short_strike: float) -> tuple[int | None, str]:
    last = len(records) - 1
    time_i = entry_i + PREMIUM_HOLD
    limit = min(time_i, last)
    for index in range(entry_i, limit + 1):
        if index == time_i:
            return index, "time"
        spot = float(records[index]["raw_close"])
        if side == 1 and spot < short_strike:
            return index, "strike_breach"
        if side == -1 and spot > short_strike:
            return index, "strike_breach"
    return None, "open"


def _exit_legs(symbol, dates, exit_date, spread: Spread, chain_getter: ChainGetter):
    if exit_date not in dates:
        return None
    start = dates.index(exit_date)
    window = dates[start : start + 1 + EXIT_QUOTE_FORWARD_SESSIONS]
    for day in window:
        status, rows = chain_getter(symbol, day)
        if status != "ok":
            continue
        long_leg = find_leg(rows, spread.expiration, spread.long_strike, spread.right)
        short_leg = find_leg(rows, spread.expiration, spread.short_strike, spread.right)
        if long_leg is not None and short_leg is not None:
            return day, long_leg, short_leg
    return None


def _option_trade(
    symbol: str,
    strategy: str,
    stock: dict,
    records: list[dict],
    entry_i: int,
    spread: Spread,
    contracts: int,
    long_bid: Decimal,
    short_ask: Decimal,
    quote_date: date,
    structure: str,
) -> dict:
        pnl, commission = option_pnl(spread, long_bid, short_ask, contracts)
        defined = spread.max_loss * Decimal(100) * contracts
        pnl_f = float(pnl)
        entry_close = float(records[entry_i]["close"])
        exit_close = float(records[stock["exit_index"]]["close"])
        underlying_return = None if entry_close == 0 else exit_close / entry_close - 1
        reason = str(stock["exit_reason"])
        if quote_date != records[stock["exit_index"]]["date"]:
            reason = f"{reason}_quote_delay"
        return {
        "result_type": "direct_option",
        "strategy": strategy,
        "symbol": symbol,
        "side": stock["side"],
        "side_sign": stock["side_sign"],
        "status": "closed",
        "signal_date": stock["signal_date"],
        "signal_index": stock["signal_index"],
        "entry_date": records[entry_i]["date"],
        "entry_index": entry_i,
        "exit_date": quote_date,
        "exit_index": stock["exit_index"],
        "exit_reason": reason,
        "structure": structure,
        "expiration": spread.expiration,
        "long_strike": spread.long_strike,
        "short_strike": spread.short_strike,
        "premium": spread.premium,
        "width": spread.width,
        "contracts": contracts,
        "max_loss": spread.max_loss,
        "risk_dollars": float(defined),
        "pnl": pnl_f,
        "r_multiple": pnl_f / float(defined),
        "trend_regime": stock.get("trend_regime") or "unknown",
        "vol_regime": stock.get("vol_regime") or "unknown",
        "entry_iv": stock.get("entry_iv"),
        "entry_rv20": stock.get("entry_rv20"),
        "iv_percentile": stock.get("iv_percentile"),
        "short_iv": None if spread.short_iv is None else float(spread.short_iv),
        "spot": float(records[entry_i]["raw_close"]),
        "underlying_return": underlying_return,
        "commissions": float(commission),
    }


def _unmarked(symbol, stock, records, entry_i, exit_i, reason, spread: Spread) -> dict:
    return {
        "result_type": "direct_option",
        "symbol": symbol,
        "strategy": stock["strategy"],
        "side": stock.get("side"),
        "signal_date": stock.get("signal_date"),
        "entry_date": records[entry_i]["date"],
        "intended_exit": records[exit_i]["date"],
        "reason": reason,
        "expiration": spread.expiration,
        "long_strike": spread.long_strike,
        "short_strike": spread.short_strike,
        "underlying_return": records[exit_i]["close"] / records[entry_i]["close"] - 1,
    }


def _skip(symbol: str, stock: dict, reason: str, gap: Decimal | None = None) -> dict:
    return {
        "result_type": "direct_option",
        "symbol": symbol,
        "strategy": stock["strategy"],
        "signal_date": stock.get("signal_date"),
        "reason": reason,
        "atm_gap": None if gap is None else float(gap),
    }


def _spot(bar: dict) -> Decimal:
    return Decimal(str(bar["raw_close"]))


def _split_between(splits: list[date], start: date, end: date) -> bool:
    return any(start < ex_date <= end for ex_date in splits)
