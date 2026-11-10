"""Price and volatility math. Each bar uses only data at or before that bar."""

from __future__ import annotations

import math
import statistics
from datetime import date


def rolling_mean(values: list[float], window: int) -> list[float | None]:
    if window <= 0:
        raise ValueError("window must be positive")
    out: list[float | None] = [None] * len(values)
    total = 0.0
    for i, value in enumerate(values):
        total += value
        if i >= window:
            total -= values[i - window]
        if i >= window - 1:
            out[i] = total / window
    return out


def rolling_std(values: list[float], window: int) -> list[float | None]:
    if window < 2:
        raise ValueError("window must be at least 2")
    out: list[float | None] = [None] * len(values)
    for i in range(window - 1, len(values)):
        win = values[i - window + 1 : i + 1]
        mean = sum(win) / window
        var = sum((x - mean) ** 2 for x in win) / (window - 1)
        out[i] = math.sqrt(var)
    return out


def prior_rolling_extreme(values: list[float], window: int, *, how: str) -> list[float | None]:
    if window <= 0:
        raise ValueError("window must be positive")
    if how not in ("max", "min"):
        raise ValueError(how)
    out: list[float | None] = [None] * len(values)
    for i in range(window, len(values)):
        win = values[i - window : i]
        out[i] = max(win) if how == "max" else min(win)
    return out


def rsi(closes: list[float], period: int) -> list[float | None]:
    """Wilder RSI. Index `period` is the first defined value."""
    if period <= 0:
        raise ValueError("period must be positive")
    out: list[float | None] = [None] * len(closes)
    if len(closes) <= period:
        return out
    gains: list[float] = []
    losses: list[float] = []
    for i in range(1, period + 1):
        change = closes[i] - closes[i - 1]
        gains.append(max(change, 0.0))
        losses.append(max(-change, 0.0))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    def _value(avg_g: float, avg_l: float) -> float:
        if avg_l == 0.0:
            return 100.0
        rs = avg_g / avg_l
        return 100.0 - (100.0 / (1.0 + rs))

    out[period] = _value(avg_gain, avg_loss)
    for i in range(period + 1, len(closes)):
        change = closes[i] - closes[i - 1]
        gain = max(change, 0.0)
        loss = max(-change, 0.0)
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        out[i] = _value(avg_gain, avg_loss)
    return out


def _true_range(high: float, low: float, prev_close: float) -> float:
    return max(high - low, abs(high - prev_close), abs(low - prev_close))


def atr(high: list[float], low: list[float], close: list[float], period: int) -> list[float | None]:
    """Wilder ATR. The first value sits on index `period`."""
    if not (len(high) == len(low) == len(close)):
        raise ValueError("OHLC lengths differ")
    if period <= 0:
        raise ValueError("period must be positive")
    out: list[float | None] = [None] * len(close)
    if len(close) <= period:
        return out
    true_ranges = [
        _true_range(high[i], low[i], close[i - 1]) for i in range(1, len(close))
    ]
    current = sum(true_ranges[:period]) / period
    out[period] = current
    for i in range(period + 1, len(close)):
        current = (current * (period - 1) + true_ranges[i - 1]) / period
        out[i] = current
    return out


def realized_vol(closes: list[float], window: int, annualization: int = 252) -> list[float | None]:
    """Annualized sample std of the last `window` log returns, ending at this bar."""
    if window < 2:
        raise ValueError("window must be at least 2")
    rets: list[float | None] = [None]
    for i in range(1, len(closes)):
        prev = closes[i - 1]
        cur = closes[i]
        if prev <= 0 or cur <= 0:
            rets.append(None)
        else:
            rets.append(math.log(cur / prev))
    out: list[float | None] = [None] * len(closes)
    for i in range(len(closes)):
        if i < window:
            continue
        win = rets[i - window + 1 : i + 1]
        if len(win) < window or any(value is None for value in win):
            continue
        nums = [float(value) for value in win if value is not None]
        mean = sum(nums) / window
        var = sum((value - mean) ** 2 for value in nums) / (window - 1)
        out[i] = math.sqrt(var * annualization)
    return out


def forward_realized_vol(
    closes: list[float],
    start_index: int,
    horizon: int,
    annualization: int = 252,
) -> float | None:
    """Annualized sample std of the next `horizon` log returns after `start_index`.

    The return on the start bar itself is not included. That return was already
    known at the close where a signal is decided.
    """
    if horizon < 2:
        raise ValueError("horizon must be at least 2")
    end = start_index + horizon
    if start_index < 0 or end >= len(closes):
        return None
    rets: list[float] = []
    for i in range(start_index + 1, end + 1):
        prev = closes[i - 1]
        cur = closes[i]
        if prev <= 0 or cur <= 0:
            return None
        rets.append(math.log(cur / prev))
    mean = sum(rets) / len(rets)
    var = sum((value - mean) ** 2 for value in rets) / (len(rets) - 1)
    return math.sqrt(var * annualization)


def expected_move(implied_vol: float, horizon_days: int, trading_days: int = 252) -> float:
    """One-standard-deviation simple-return move, `iv * sqrt(horizon / year)`."""
    if implied_vol < 0 or horizon_days < 0 or trading_days <= 0:
        raise ValueError("invalid expected-move inputs")
    return implied_vol * math.sqrt(horizon_days / trading_days)


def trailing_percentile_complete(values: list[float], window: int) -> list[float | None]:
    """Fraction of the inclusive trailing window that is <= the current value.

    `values[i]` is ranked only against `values[i-window+1 : i+1]`.
    """
    if window <= 0:
        raise ValueError("window must be positive")
    out: list[float | None] = [None] * len(values)
    for i in range(window - 1, len(values)):
        win = values[i - window + 1 : i + 1]
        current = win[-1]
        out[i] = sum(1 for value in win if value <= current) / window
    return out


def trailing_median_exclusive(values: list[float | None], window: int) -> list[float | None]:
    """Median of the prior `window` readings, excluding the current bar."""
    if window <= 0:
        raise ValueError("window must be positive")
    out: list[float | None] = [None] * len(values)
    for i in range(window, len(values)):
        win = values[i - window : i]
        if any(value is None for value in win):
            continue
        nums = [float(value) for value in win if value is not None]
        out[i] = float(statistics.median(nums))
    return out


def percentile_by_date(points: list[tuple[date, float]], window: int) -> dict[date, float]:
    ordered = sorted(points, key=lambda item: item[0])
    values = [value for _, value in ordered]
    ranks = trailing_percentile_complete(values, window)
    return {
        ordered[i][0]: float(ranks[i])
        for i in range(len(ordered))
        if ranks[i] is not None
    }
