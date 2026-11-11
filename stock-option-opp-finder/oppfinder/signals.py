"""Entry rules shared by the backtest and the scanner."""

from __future__ import annotations

from dataclasses import dataclass

from oppfinder.config import (
    BREAKOUT_VOL_MULT,
    IV_PERCENTILE_MIN,
    MR_RSI_LONG,
    MR_RSI_SHORT,
    BB_MULT,
)

TREND = "trend_continuation"
MEAN_REVERSION = "mean_reversion"
BREAKOUT = "momentum_breakout"
PREMIUM = "high_iv_premium"


@dataclass(frozen=True)
class Clause:
    name: str
    passed: bool
    detail: str


def pattern_matches(clauses: list[Clause]) -> bool:
    return bool(clauses) and all(clause.passed for clause in clauses)


def match_explanation(clauses: list[Clause]) -> str:
    passed = [clause for clause in clauses if clause.passed]
    if not passed:
        return "no clause passed"
    return "; ".join(f"{clause.name} ({clause.detail})" for clause in passed)


def _fmt(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}"


def _num(bar: dict, key: str) -> float | None:
    value = bar.get(key)
    if value is None:
        return None
    return float(value)


def _side(long_clauses: list[Clause], short_clauses: list[Clause]) -> int:
    long_ok = pattern_matches(long_clauses)
    short_ok = pattern_matches(short_clauses)
    if long_ok and short_ok:
        return 0
    if long_ok:
        return 1
    if short_ok:
        return -1
    return 0


def trend_long_clauses(records: list[dict], index: int) -> list[Clause]:
    if index < 1:
        return [Clause("history", False, "need a prior bar")]
    bar = records[index]
    prev = records[index - 1]
    close = _num(bar, "close")
    sma50 = _num(bar, "sma50")
    sma20 = _num(bar, "sma20")
    slope = _num(bar, "sma50_lag20")
    prev_close = _num(prev, "close")
    prev_sma20 = _num(prev, "sma20")
    return [
        Clause(
            "close_above_sma50",
            close is not None and sma50 is not None and close > sma50,
            f"close {_fmt(close)} vs SMA50 {_fmt(sma50)}",
        ),
        Clause(
            "sma50_rising",
            sma50 is not None and slope is not None and sma50 > slope,
            f"SMA50 {_fmt(sma50)} vs SMA50 20 sessions ago {_fmt(slope)}",
        ),
        Clause(
            "cross_above_sma20",
            prev_close is not None
            and prev_sma20 is not None
            and close is not None
            and sma20 is not None
            and prev_close <= prev_sma20
            and close > sma20,
            f"prior close {_fmt(prev_close)} vs prior SMA20 {_fmt(prev_sma20)}; close {_fmt(close)} vs SMA20 {_fmt(sma20)}",
        ),
    ]


def trend_short_clauses(records: list[dict], index: int) -> list[Clause]:
    if index < 1:
        return [Clause("history", False, "need a prior bar")]
    bar = records[index]
    prev = records[index - 1]
    close = _num(bar, "close")
    sma50 = _num(bar, "sma50")
    sma20 = _num(bar, "sma20")
    slope = _num(bar, "sma50_lag20")
    prev_close = _num(prev, "close")
    prev_sma20 = _num(prev, "sma20")
    return [
        Clause(
            "close_below_sma50",
            close is not None and sma50 is not None and close < sma50,
            f"close {_fmt(close)} vs SMA50 {_fmt(sma50)}",
        ),
        Clause(
            "sma50_falling",
            sma50 is not None and slope is not None and sma50 < slope,
            f"SMA50 {_fmt(sma50)} vs SMA50 20 sessions ago {_fmt(slope)}",
        ),
        Clause(
            "cross_below_sma20",
            prev_close is not None
            and prev_sma20 is not None
            and close is not None
            and sma20 is not None
            and prev_close >= prev_sma20
            and close < sma20,
            f"prior close {_fmt(prev_close)} vs prior SMA20 {_fmt(prev_sma20)}; close {_fmt(close)} vs SMA20 {_fmt(sma20)}",
        ),
    ]


def trend_side(records: list[dict], index: int) -> int:
    return _side(trend_long_clauses(records, index), trend_short_clauses(records, index))


def _bands(bar: dict) -> tuple[float | None, float | None]:
    sma20 = _num(bar, "sma20")
    std20 = _num(bar, "std20")
    if sma20 is None or std20 is None:
        return None, None
    return sma20 - BB_MULT * std20, sma20 + BB_MULT * std20


def mean_reversion_long_clauses(records: list[dict], index: int) -> list[Clause]:
    bar = records[index]
    close = _num(bar, "close")
    sma200 = _num(bar, "sma200")
    rsi2 = _num(bar, "rsi2")
    lower, _upper = _bands(bar)
    return [
        Clause(
            "close_above_sma200",
            close is not None and sma200 is not None and close > sma200,
            f"close {_fmt(close)} vs SMA200 {_fmt(sma200)}",
        ),
        Clause(
            "rsi2_stretched",
            rsi2 is not None and rsi2 < MR_RSI_LONG,
            f"RSI(2) {_fmt(rsi2)} < {MR_RSI_LONG:.0f}",
        ),
        Clause(
            "below_lower_band",
            close is not None and lower is not None and close < lower,
            f"close {_fmt(close)} vs lower band {_fmt(lower)}",
        ),
    ]


def mean_reversion_short_clauses(records: list[dict], index: int) -> list[Clause]:
    bar = records[index]
    close = _num(bar, "close")
    sma200 = _num(bar, "sma200")
    rsi2 = _num(bar, "rsi2")
    _lower, upper = _bands(bar)
    return [
        Clause(
            "close_below_sma200",
            close is not None and sma200 is not None and close < sma200,
            f"close {_fmt(close)} vs SMA200 {_fmt(sma200)}",
        ),
        Clause(
            "rsi2_stretched_up",
            rsi2 is not None and rsi2 > MR_RSI_SHORT,
            f"RSI(2) {_fmt(rsi2)} > {MR_RSI_SHORT:.0f}",
        ),
        Clause(
            "above_upper_band",
            close is not None and upper is not None and close > upper,
            f"close {_fmt(close)} vs upper band {_fmt(upper)}",
        ),
    ]


def mean_reversion_side(records: list[dict], index: int) -> int:
    return _side(
        mean_reversion_long_clauses(records, index),
        mean_reversion_short_clauses(records, index),
    )


def breakout_long_clauses(records: list[dict], index: int) -> list[Clause]:
    bar = records[index]
    close = _num(bar, "close")
    sma50 = _num(bar, "sma50")
    prior_high = _num(bar, "prior_high20")
    volume = _num(bar, "volume")
    prior_vol = _num(bar, "prior_vol20")
    return [
        Clause(
            "close_above_prior_20_high",
            close is not None and prior_high is not None and close > prior_high,
            f"close {_fmt(close)} vs prior 20-session high {_fmt(prior_high)}",
        ),
        Clause(
            "close_above_sma50",
            close is not None and sma50 is not None and close > sma50,
            f"close {_fmt(close)} vs SMA50 {_fmt(sma50)}",
        ),
        Clause(
            "volume_expansion",
            volume is not None and prior_vol is not None and prior_vol > 0 and volume > BREAKOUT_VOL_MULT * prior_vol,
            f"volume {_fmt(volume, 0)} vs {BREAKOUT_VOL_MULT:.1f}x prior 20-session average {_fmt(prior_vol, 0)}",
        ),
    ]


def breakout_short_clauses(records: list[dict], index: int) -> list[Clause]:
    bar = records[index]
    close = _num(bar, "close")
    sma50 = _num(bar, "sma50")
    prior_low = _num(bar, "prior_low20")
    volume = _num(bar, "volume")
    prior_vol = _num(bar, "prior_vol20")
    return [
        Clause(
            "close_below_prior_20_low",
            close is not None and prior_low is not None and close < prior_low,
            f"close {_fmt(close)} vs prior 20-session low {_fmt(prior_low)}",
        ),
        Clause(
            "close_below_sma50",
            close is not None and sma50 is not None and close < sma50,
            f"close {_fmt(close)} vs SMA50 {_fmt(sma50)}",
        ),
        Clause(
            "volume_expansion",
            volume is not None and prior_vol is not None and prior_vol > 0 and volume > BREAKOUT_VOL_MULT * prior_vol,
            f"volume {_fmt(volume, 0)} vs {BREAKOUT_VOL_MULT:.1f}x prior 20-session average {_fmt(prior_vol, 0)}",
        ),
    ]


def breakout_side(records: list[dict], index: int) -> int:
    return _side(breakout_long_clauses(records, index), breakout_short_clauses(records, index))


def premium_long_clauses(records: list[dict], index: int) -> list[Clause]:
    """Bullish defined-risk premium: short put vertical when IV is rich and price is above SMA50."""
    bar = records[index]
    iv = _num(bar, "iv")
    iv_pct = _num(bar, "iv_pct")
    rv20 = _num(bar, "rv20")
    close = _num(bar, "close")
    sma50 = _num(bar, "sma50")
    return [
        Clause(
            "iv_percentile",
            iv_pct is not None and iv_pct >= IV_PERCENTILE_MIN,
            f"IV percentile {_fmt(iv_pct, 2)} vs minimum {IV_PERCENTILE_MIN:.2f}",
        ),
        Clause(
            "iv_above_realized",
            iv is not None and rv20 is not None and iv > rv20,
            f"IV {_fmt(iv, 4)} vs 20-day realized vol {_fmt(rv20, 4)}",
        ),
        Clause(
            "close_above_sma50",
            close is not None and sma50 is not None and close > sma50,
            f"close {_fmt(close)} vs SMA50 {_fmt(sma50)}",
        ),
    ]


def premium_short_clauses(records: list[dict], index: int) -> list[Clause]:
    """Bearish defined-risk premium: short call vertical when IV is rich and price is below SMA50."""
    bar = records[index]
    iv = _num(bar, "iv")
    iv_pct = _num(bar, "iv_pct")
    rv20 = _num(bar, "rv20")
    close = _num(bar, "close")
    sma50 = _num(bar, "sma50")
    return [
        Clause(
            "iv_percentile",
            iv_pct is not None and iv_pct >= IV_PERCENTILE_MIN,
            f"IV percentile {_fmt(iv_pct, 2)} vs minimum {IV_PERCENTILE_MIN:.2f}",
        ),
        Clause(
            "iv_above_realized",
            iv is not None and rv20 is not None and iv > rv20,
            f"IV {_fmt(iv, 4)} vs 20-day realized vol {_fmt(rv20, 4)}",
        ),
        Clause(
            "close_below_sma50",
            close is not None and sma50 is not None and close < sma50,
            f"close {_fmt(close)} vs SMA50 {_fmt(sma50)}",
        ),
    ]


def premium_side(records: list[dict], index: int) -> int:
    return _side(premium_long_clauses(records, index), premium_short_clauses(records, index))


def trend_invalid(bar: dict, side: int, _level: float | None = None) -> bool:
    close = _num(bar, "close")
    sma50 = _num(bar, "sma50")
    if close is None or sma50 is None:
        return False
    if side == 1:
        return close < sma50
    if side == -1:
        return close > sma50
    raise ValueError(side)


def mean_reversion_invalid(bar: dict, side: int, _level: float | None = None) -> bool:
    """Exit when price has reverted through the 20-day average."""
    close = _num(bar, "close")
    sma20 = _num(bar, "sma20")
    if close is None or sma20 is None:
        return False
    if side == 1:
        return close > sma20
    if side == -1:
        return close < sma20
    raise ValueError(side)


def breakout_invalid(bar: dict, side: int, level: float | None) -> bool:
    close = _num(bar, "close")
    if close is None or level is None:
        return False
    if side == 1:
        return close < level
    if side == -1:
        return close > level
    raise ValueError(side)


def breakout_level(records: list[dict], index: int, side: int) -> float | None:
    bar = records[index]
    if side == 1:
        return _num(bar, "prior_high20")
    if side == -1:
        return _num(bar, "prior_low20")
    raise ValueError(side)


def no_level(_records: list[dict], _index: int, _side: int) -> float | None:
    return None
