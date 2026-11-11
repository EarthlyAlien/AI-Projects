"""Optional sentiment filter. A missing score never becomes a fabricated pass."""

from __future__ import annotations

from datetime import date

from oppfinder.signals import BREAKOUT, MEAN_REVERSION, PREMIUM, TREND


def sentiment_allows(
    kind: str,
    strategy: str,
    side: int,
    score: float | None,
    median: float | None,
    low_decile: float | None,
) -> bool:
    """Precommitted filter. `score is None` blocks the entry instead of inventing a value.

    put_call: higher means more put buying. Mean-reversion longs require a fearful
    reading; premium selling is blocked in that same fearful bucket.
    news_tone: higher means more positive coverage. Directional trades need the
    tone to agree with the side. Premium selling is blocked in the bottom decile.
    fear_greed: 0 is fear and 100 is greed, using the CNN scale.
    """
    if score is None or side == 0:
        return False
    if kind == "put_call":
        if median is None:
            return False
        if strategy == MEAN_REVERSION and side == 1:
            return score >= median
        if strategy == PREMIUM:
            return score <= median
        return True
    if kind == "news_tone":
        if strategy == PREMIUM:
            if low_decile is None:
                return False
            return score > low_decile
        if side == 1:
            return score >= 0
        return score <= 0
    if kind == "fear_greed":
        if strategy == MEAN_REVERSION and side == 1:
            return score <= 40
        if strategy == MEAN_REVERSION and side == -1:
            return score >= 60
        if strategy == PREMIUM:
            return score >= 30
        if strategy in (TREND, BREAKOUT) and side == 1:
            return score >= 50
        if strategy in (TREND, BREAKOUT) and side == -1:
            return score <= 50
        return False
    raise ValueError(kind)


def mask_side(base, kind: str, strategy: str, scores: dict[date, float], medians: dict[date, float], deciles: dict[date, float]):
    def _side(records: list[dict], index: int) -> int:
        side = base(records, index)
        if side == 0:
            return 0
        day = records[index]["date"]
        if sentiment_allows(kind, strategy, side, scores.get(day), medians.get(day), deciles.get(day)):
            return side
        return 0

    return _side
