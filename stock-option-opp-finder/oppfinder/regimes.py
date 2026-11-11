"""Trend and volatility regime labels. A bar can carry one of each."""

from __future__ import annotations

from typing import Literal

TrendRegime = Literal["uptrend", "downtrend", "range", "unknown"]
VolRegime = Literal["high_vol", "low_vol", "unknown"]


def trend_regime(close: float | None, sma50: float | None, sma200: float | None) -> TrendRegime:
    if close is None or sma50 is None or sma200 is None:
        return "unknown"
    if close > sma200 and sma50 > sma200:
        return "uptrend"
    if close < sma200 and sma50 < sma200:
        return "downtrend"
    return "range"


def vol_regime(rv20: float | None, rv_median: float | None) -> VolRegime:
    """High vol means today's 20-day realized vol is at or above its prior median."""
    if rv20 is None or rv_median is None:
        return "unknown"
    if rv20 >= rv_median:
        return "high_vol"
    return "low_vol"
