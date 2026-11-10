"""Last-session scan. A match is not a recommendation."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from oppfinder.config import ATR_STOP_MULT, EQUITY0, OPTION_SYMBOLS, RISK_FRAC
from oppfinder.options_backtest import ChainGetter
from oppfinder.signals import (
    BREAKOUT,
    MEAN_REVERSION,
    PREMIUM,
    TREND,
    breakout_long_clauses,
    breakout_short_clauses,
    match_explanation,
    mean_reversion_long_clauses,
    mean_reversion_short_clauses,
    pattern_matches,
    premium_long_clauses,
    premium_short_clauses,
    trend_long_clauses,
    trend_short_clauses,
)
from oppfinder.spreads import build_credit_vertical, build_debit_vertical
from oppfinder.config import BREAKOUT_DTE, MR_DTE, PREMIUM_DTE, TREND_DTE

_LONG = {
    TREND: trend_long_clauses,
    MEAN_REVERSION: mean_reversion_long_clauses,
    BREAKOUT: breakout_long_clauses,
    PREMIUM: premium_long_clauses,
}
_SHORT = {
    TREND: trend_short_clauses,
    MEAN_REVERSION: mean_reversion_short_clauses,
    BREAKOUT: breakout_short_clauses,
    PREMIUM: premium_short_clauses,
}
_DTE = {TREND: TREND_DTE, MEAN_REVERSION: MR_DTE, BREAKOUT: BREAKOUT_DTE}


def build_scan(
    frames: dict[str, list[dict]],
    summaries: list[dict],
    chain_getter: ChainGetter,
    last_session: date,
) -> list[dict]:
    rows: list[dict] = []
    for symbol, records in sorted(frames.items()):
        if not records or records[-1]["date"] != last_session:
            continue
        index = len(records) - 1
        for strategy in (TREND, MEAN_REVERSION, BREAKOUT, PREMIUM):
            if index < 1 and strategy == TREND:
                continue
            long_clauses = _LONG[strategy](records, index)
            short_clauses = _SHORT[strategy](records, index)
            long_ok = pattern_matches(long_clauses)
            short_ok = pattern_matches(short_clauses)
            if long_ok == short_ok:
                continue
            side = 1 if long_ok else -1
            clauses = long_clauses if side == 1 else short_clauses
            history = _history(summaries, strategy, symbol)
            illustrative, illustration_note = _illustrate(symbol, records[index], strategy, side, chain_getter, last_session)
            rows.append(
                {
                    "symbol": symbol,
                    "strategy": strategy,
                    "side": "long" if side == 1 else "short",
                    "as_of": last_session.isoformat(),
                    "supported": history["evidence"] == "positive_interval_above_zero",
                    "why": match_explanation(clauses),
                    "history_result_type": history["result_type"],
                    "historical_n": history["n"],
                    "historical_mean_r": history["mean_r"],
                    "historical_expectancy": history["expectancy"],
                    "historical_profit_factor": history["profit_factor"],
                    "evidence": history["evidence"],
                    "evidence_note": history["note"],
                    "invalidation": _invalidation(strategy, side, records[index]),
                    "max_loss": _max_loss(strategy, records[index], illustrative),
                    "pass_if": _pass_if(strategy, side, records[index]),
                    "illustrative_structure": illustrative,
                    "illustration_note": illustration_note,
                    "close": records[index]["close"],
                    "atr14": records[index].get("atr14"),
                    "iv": records[index].get("iv"),
                    "iv_pct": records[index].get("iv_pct"),
                    "rv20": records[index].get("rv20"),
                    "trend_regime": records[index].get("trend_regime"),
                    "vol_regime": records[index].get("vol_regime"),
                }
            )
    rows.sort(key=lambda row: (not row["supported"], row["symbol"], row["strategy"]))
    return rows


def _history(summaries: list[dict], strategy: str, symbol: str) -> dict:
    direct = _find(summaries, "direct_option", strategy)
    proxy = _find(summaries, "underlying_proxy", strategy)
    if symbol in OPTION_SYMBOLS and direct is not None:
        return direct
    if proxy is not None:
        return proxy
    return {
        "result_type": "untested",
        "n": 0,
        "mean_r": None,
        "expectancy": None,
        "profit_factor": None,
        "evidence": "too_small",
        "note": "This strategy was not run for the available data.",
    }


def _find(summaries: list[dict], result_type: str, strategy: str) -> dict | None:
    for row in summaries:
        if row["result_type"] == result_type and row["strategy"] == strategy:
            return row
    return None


def _illustrate(symbol, bar, strategy, side, chain_getter: ChainGetter, last_session: date):
    note = (
        "Illustration uses the signal session's end-of-day chain. "
        "The backtest would enter on the next session's chain, which is not a completed print yet."
    )
    if symbol not in OPTION_SYMBOLS:
        return None, "No listed-chain history for this symbol in the free dataset, so there is no structure to illustrate."
    status, rows = chain_getter(symbol, last_session)
    if status != "ok":
        return None, f"Chain lookup for {last_session.isoformat()} returned {status}."
    spot = Decimal(str(bar["raw_close"]))
    if strategy == PREMIUM:
        right = "PUT" if side == 1 else "CALL"
        spread, reason = build_credit_vertical(rows, spot, last_session, right, PREMIUM_DTE)
    else:
        right = "CALL" if side == 1 else "PUT"
        spread, reason = build_debit_vertical(rows, last_session, right, _DTE[strategy])
    if spread is None:
        return None, f"Signal-day chain did not produce a valid one-strike vertical ({reason})."
    return (
        {
            "kind": spread.kind,
            "right": spread.right,
            "expiration": spread.expiration.isoformat(),
            "long_strike": float(spread.long_strike),
            "short_strike": float(spread.short_strike),
            "premium": float(spread.premium),
            "width": float(spread.width),
            "max_loss_per_share": float(spread.max_loss),
            "max_profit_per_share": float(spread.max_profit),
        },
        note,
    )


def _fmt(value) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.2f}"


def _invalidation(strategy: str, side: int, bar: dict) -> str:
    if strategy == TREND:
        level = _fmt(bar.get("sma50"))
        if side == 1:
            return f"Close back below the 50-day average ({level})."
        return f"Close back above the 50-day average ({level})."
    if strategy == MEAN_REVERSION:
        level = _fmt(bar.get("sma20"))
        if side == 1:
            return f"The long is there to revert through the 20-day average ({level}). A close that does not reclaim it within 5 sessions ends the trade; the hard stop is 2 ATR."
        return f"The short is there to revert through the 20-day average ({level}) within 5 sessions. The hard stop is 2 ATR."
    if strategy == BREAKOUT:
        level = bar.get("prior_high20") if side == 1 else bar.get("prior_low20")
        return f"Close back through the broken 20-session level ({_fmt(level)})."
    if strategy == PREMIUM:
        return "Underlying close through the short strike of the credit vertical. That strike is chosen from the entry chain, not from this signal bar."
    raise ValueError(strategy)


def _max_loss(strategy: str, bar: dict, illustrative: dict | None) -> str:
    atr = bar.get("atr14")
    stock = (
        f"Stock proxy risk is {RISK_FRAC:.0%} of ${EQUITY0:,.0f} "
        f"(${EQUITY0 * RISK_FRAC:,.0f}) with a {ATR_STOP_MULT:.0f} ATR stop"
    )
    if atr is not None:
        stock += f" (ATR14 is {_fmt(atr)})."
    else:
        stock += "."
    if strategy == PREMIUM:
        stock = "There is no stock-stop version of premium selling in this test."
    if illustrative is None:
        return stock + " No listed vertical was priced from the signal-day chain."
    per = illustrative["max_loss_per_share"] * 100
    return (
        f"{stock} Illustrated one-lot vertical max loss is ${per:,.2f} before commissions "
        f"({illustrative['kind']} {illustrative['right'].lower()}, width {illustrative['width']:.2f}, "
        f"premium {illustrative['premium']:.2f})."
    )


def _pass_if(strategy: str, side: int, bar: dict) -> str:
    atr = _fmt(bar.get("atr14"))
    if strategy == TREND:
        return (
            f"Pass if the next open is already through the {ATR_STOP_MULT:.0f} ATR stop "
            f"(ATR14 {atr}), if the close is no longer on the signal side of the 50-day average, "
            "or if the entry chain cannot build a one-strike debit vertical inside the risk budget."
        )
    if strategy == MEAN_REVERSION:
        return (
            "Pass if the next open gaps through the 2 ATR stop, if the stretch (RSI(2) and the Bollinger band) "
            "has already snapped back before entry, or if no valid debit vertical is on the entry chain."
        )
    if strategy == BREAKOUT:
        level = bar.get("prior_high20") if side == 1 else bar.get("prior_low20")
        return (
            f"Pass if price is back through {_fmt(level)} before entry, if the next open gaps through the 2 ATR stop, "
            "or if the entry chain has no one-strike debit vertical inside the risk budget."
        )
    if strategy == PREMIUM:
        return (
            "Pass if IV percentile is back under 0.60, if IV is no longer above 20-day realized vol, "
            "if the underlying is already through the short strike, or if one contract's width-minus-credit "
            "loss exceeds 2.5% of the $100,000 reference."
        )
    raise ValueError(strategy)
