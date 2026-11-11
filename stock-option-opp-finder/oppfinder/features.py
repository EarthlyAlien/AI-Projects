"""Attach indicators and regime labels. Nothing here reads a later bar."""

from __future__ import annotations

from datetime import date

from oppfinder.config import (
    ATR_PERIOD,
    BB_WINDOW,
    BREAKOUT_LOOKBACK,
    IV_PCT_WINDOW,
    RSI_PERIOD,
    RV_MEDIAN_WINDOW,
    RV_WINDOW,
    SMA_FAST,
    SMA_MID,
    SMA_SLOW,
    SMA_SLOPE_LAG,
)
from oppfinder.indicators import (
    atr,
    percentile_by_date,
    prior_rolling_extreme,
    realized_vol,
    rolling_mean,
    rolling_std,
    rsi,
    trailing_median_exclusive,
)
from oppfinder.regimes import trend_regime, vol_regime


def build_records(
    bars: list[dict],
    iv_points: list[tuple[date, float]] | None = None,
) -> list[dict]:
    ordered = _dedupe(bars)
    closes = [float(bar["close"]) for bar in ordered]
    highs = [float(bar["high"]) for bar in ordered]
    lows = [float(bar["low"]) for bar in ordered]
    volumes = [float(bar["volume"]) for bar in ordered]
    sma20 = rolling_mean(closes, SMA_FAST)
    sma50 = rolling_mean(closes, SMA_MID)
    sma200 = rolling_mean(closes, SMA_SLOW)
    sma50_lag = _lag(sma50, SMA_SLOPE_LAG)
    std20 = rolling_std(closes, BB_WINDOW)
    atr14 = atr(highs, lows, closes, ATR_PERIOD)
    rsi2 = rsi(closes, RSI_PERIOD)
    rv20 = realized_vol(closes, RV_WINDOW)
    rv_median = trailing_median_exclusive(rv20, RV_MEDIAN_WINDOW)
    prior_high = prior_rolling_extreme(highs, BREAKOUT_LOOKBACK, how="max")
    prior_low = prior_rolling_extreme(lows, BREAKOUT_LOOKBACK, how="min")
    prior_vol = _prior_mean(volumes, BREAKOUT_LOOKBACK)
    iv_map = {day: value for day, value in (iv_points or [])}
    iv_pct = percentile_by_date(iv_points or [], IV_PCT_WINDOW)
    records: list[dict] = []
    for i, bar in enumerate(ordered):
        day = bar["date"]
        close = closes[i]
        records.append(
            {
                "date": day,
                "open": float(bar["open"]),
                "high": highs[i],
                "low": lows[i],
                "close": close,
                "volume": volumes[i],
                "raw_close": float(bar.get("raw_close", close)),
                "sma20": sma20[i],
                "sma50": sma50[i],
                "sma200": sma200[i],
                "sma50_lag20": sma50_lag[i],
                "std20": std20[i],
                "atr14": atr14[i],
                "rsi2": rsi2[i],
                "rv20": rv20[i],
                "rv_median": rv_median[i],
                "prior_high20": prior_high[i],
                "prior_low20": prior_low[i],
                "prior_vol20": prior_vol[i],
                "iv": iv_map.get(day),
                "iv_pct": iv_pct.get(day),
                "trend_regime": trend_regime(close, sma50[i], sma200[i]),
                "vol_regime": vol_regime(rv20[i], rv_median[i]),
            }
        )
    return records


def with_external_iv(records: list[dict], iv_points: list[tuple[date, float]]) -> list[dict]:
    """Copy records and replace IV fields. Price indicators stay as they were."""
    iv_map = {day: value for day, value in iv_points}
    iv_pct = percentile_by_date(iv_points, IV_PCT_WINDOW)
    copied: list[dict] = []
    for record in records:
        row = dict(record)
        row["iv"] = iv_map.get(record["date"])
        row["iv_pct"] = iv_pct.get(record["date"])
        copied.append(row)
    return copied


def _dedupe(bars: list[dict]) -> list[dict]:
    by_date: dict[date, dict] = {}
    for bar in bars:
        by_date[bar["date"]] = bar
    return [by_date[day] for day in sorted(by_date)]


def _lag(values: list[float | None], periods: int) -> list[float | None]:
    out: list[float | None] = [None] * len(values)
    for i in range(periods, len(values)):
        out[i] = values[i - periods]
    return out


def _prior_mean(values: list[float], window: int) -> list[float | None]:
    out: list[float | None] = [None] * len(values)
    for i in range(window, len(values)):
        win = values[i - window : i]
        out[i] = sum(win) / window
    return out
