from datetime import date, timedelta

import pytest

from oppfinder.engine import apply_slippage, run_protected_trades
from oppfinder.features import build_records
from oppfinder.indicators import (
    atr,
    expected_move,
    forward_realized_vol,
    prior_rolling_extreme,
    realized_vol,
    rolling_mean,
    rsi,
    trailing_median_exclusive,
    trailing_percentile_complete,
)
from oppfinder.regimes import trend_regime, vol_regime
from oppfinder.report import headline_sentence
from oppfinder.sentiment import sentiment_allows
from oppfinder.signals import pattern_matches, trend_long_clauses, trend_side
from oppfinder.stats import (
    average_loss,
    average_win,
    evidence_label,
    expectancy,
    max_drawdown,
    profit_factor,
    select_headline,
    summarize,
    win_rate,
)
from oppfinder.vrp import variance_risk_observations


def test_expectancy_matches_win_loss_identity():
    pnls = [2.0, -1.0, 0.0, 3.0, -4.0]
    assert expectancy(pnls) == pytest.approx(sum(pnls) / len(pnls))
    assert win_rate(pnls) == pytest.approx(2 / 5)
    assert average_win(pnls) == pytest.approx(2.5)
    assert average_loss(pnls) == pytest.approx(-2.5)
    loss_rate = 2 / 5
    assert expectancy(pnls) == pytest.approx(win_rate(pnls) * average_win(pnls) + loss_rate * average_loss(pnls))


def test_profit_factor_is_undefined_without_a_loss():
    assert profit_factor([1.0, 2.0]) is None
    assert profit_factor([2.0, 2.0, -1.0, -1.0]) == pytest.approx(2.0)


def test_max_drawdown_peak_to_trough():
    assert max_drawdown([100, 120, 90]) == pytest.approx(0.25)


def test_regimes():
    assert trend_regime(110, 105, 100) == "uptrend"
    assert trend_regime(90, 95, 100) == "downtrend"
    assert trend_regime(101, 99, 100) == "range"
    assert trend_regime(None, 1, 1) == "unknown"
    assert vol_regime(0.3, 0.2) == "high_vol"
    assert vol_regime(0.2, 0.2) == "high_vol"
    assert vol_regime(0.1, 0.2) == "low_vol"
    assert vol_regime(None, 0.2) == "unknown"


def test_percentile_does_not_read_the_future():
    base = trailing_percentile_complete([1, 2, 3, 4, 5], 3)
    changed = trailing_percentile_complete([1, 2, 3, 4, 0], 3)
    assert base[2] == changed[2] == 1.0
    assert base[4] == 1.0
    assert changed[4] == pytest.approx(1 / 3)


def test_rolling_mean_and_prior_extreme():
    assert rolling_mean([1, 2, 3, 4], 2) == [None, 1.5, 2.5, 3.5]
    assert prior_rolling_extreme([1, 5, 2, 4], 2, how="max") == [None, None, 5, 5]


def test_rsi_of_a_rising_series_is_100():
    values = rsi([float(i) for i in range(1, 12)], 2)
    assert values[2] == 100.0
    assert values[-1] == 100.0


def test_atr_period_one():
    values = atr([10, 12, 11], [9, 10, 10], [9.5, 11, 10.5], 1)
    assert values[1] == pytest.approx(2.5)
    assert values[2] == pytest.approx(1.0)


def test_expected_move_and_forward_vol_use_only_the_future_window():
    assert expected_move(0.20, 15, 252) == pytest.approx(0.20 * (15 / 252) ** 0.5)
    closes = [100.0, 110.0, 100.0, 100.0]
    # Changing the first close would change a backward vol, not this forward window's start.
    forward = forward_realized_vol(closes, 0, 2)
    assert forward == pytest.approx(realized_vol(closes[:3], 2)[2])


def test_trailing_median_excludes_today():
    medians = trailing_median_exclusive([1, 3, 100], 2)
    assert medians[2] == pytest.approx(2.0)


def test_pattern_match_requires_every_clause():
    records = [
        {"close": 9.0, "sma20": 10.0, "sma50": 8.0, "sma50_lag20": 7.0},
        {"close": 11.0, "sma20": 10.0, "sma50": 9.0, "sma50_lag20": 8.0},
    ]
    assert pattern_matches(trend_long_clauses(records, 1))
    records[1]["close"] = 9.0
    assert not pattern_matches(trend_long_clauses(records, 1))


def test_indicator_signal_ignores_a_later_bar():
    def bars(last_close: float):
        rows = []
        start = date(2024, 1, 1)
        for i in range(80):
            close = 100 + i * 0.1
            if i == 79:
                close = last_close
            rows.append(
                {
                    "date": start + timedelta(days=i),
                    "open": close,
                    "high": close + 1,
                    "low": close - 1,
                    "close": close,
                    "volume": 1_000_000,
                    "raw_close": close,
                }
            )
        return build_records(rows)

    base = bars(107.9)
    shocked = bars(1.0)
    for index in range(70):
        assert base[index]["sma50"] == shocked[index]["sma50"]
        assert trend_side(base, index) == trend_side(shocked, index)


def test_evidence_and_headline_do_not_crown_a_small_sample():
    assert evidence_label(10, 1.0, (0.5, 1.5)) == "too_small"
    assert evidence_label(40, 1.0, (0.2, 1.8)) == "positive_interval_above_zero"
    assert evidence_label(40, 0.2, (-0.1, 0.5)) == "positive_interval_includes_zero"
    small = {
        "result_type": "direct_option",
        "strategy": "momentum_breakout",
        "n": 10,
        "mean_r": 5,
        "ci95_low": 4,
        "evidence": "too_small",
    }
    soft = {
        "result_type": "direct_option",
        "strategy": "trend_continuation",
        "n": 40,
        "mean_r": 0.2,
        "ci95_low": -0.1,
        "ci95_high": 0.5,
        "evidence": "positive_interval_includes_zero",
        "note": "interval includes zero",
    }
    choice = select_headline([small, soft])
    assert choice["status"] == "positive_not_significant"
    assert choice["row"]["strategy"] == "trend_continuation"
    text = headline_sentence(choice["status"], choice["row"], "listed-option")
    assert "clearest supported" not in text
    assert "interval includes zero" in text
    wide = {
        "result_type": "direct_option",
        "strategy": "wide",
        "n": 40,
        "mean_r": 2.0,
        "ci95_low": 0.1,
        "ci95_high": 3.9,
        "evidence": "positive_interval_above_zero",
        "win_rate": 0.6,
        "expectancy": 10,
        "profit_factor": 1.4,
        "note": "supported note",
    }
    tight = {**wide, "strategy": "tight", "mean_r": 0.5, "ci95_low": 0.4, "ci95_high": 0.6}
    assert select_headline([wide, tight])["row"]["strategy"] == "tight"
    assert "clearest supported" in headline_sentence("supported", tight, "listed-option")
    assert "None is treated as a winner" in headline_sentence("all_samples_too_small", None, "listed-option")
    assert select_headline([])["status"] == "no_trades"


def test_summarize_drawdown_uses_exit_order_dollars():
    trades = [
        _closed(100.0, 1.0, date(2026, 1, 2), "uptrend", "low_vol"),
        _closed(-250.0, -2.5, date(2026, 1, 3), "uptrend", "high_vol"),
    ]
    stats = summarize(trades)
    assert stats["n"] == 2
    assert stats["expectancy"] == pytest.approx(-75.0)
    assert stats["max_drawdown"] == pytest.approx(250 / 100100)
    assert stats["by_trend"]["uptrend"]["n"] == 2
    assert stats["by_vol"]["high_vol"]["n"] == 1


def _closed(pnl, r_multiple, exit_date, trend, vol):
    return {
        "status": "closed",
        "pnl": pnl,
        "r_multiple": r_multiple,
        "exit_date": exit_date,
        "entry_date": exit_date,
        "symbol": "SPY",
        "trend_regime": trend,
        "vol_regime": vol,
        "risk_dollars": 100.0,
    }


def test_sentiment_filter_refuses_a_missing_score():
    assert sentiment_allows("news_tone", "trend_continuation", 1, None, 0.0, -1.0) is False
    assert sentiment_allows("news_tone", "trend_continuation", 1, 0.2, None, None) is True
    assert sentiment_allows("news_tone", "trend_continuation", 1, -0.2, None, None) is False
    assert sentiment_allows("put_call", "mean_reversion", 1, 0.8, 0.7, None) is True
    assert sentiment_allows("put_call", "high_iv_premium", 1, 0.9, 0.7, None) is False
    assert sentiment_allows("fear_greed", "mean_reversion", 1, 25, None, None) is True
    assert sentiment_allows("fear_greed", "momentum_breakout", 1, 40, None, None) is False


def test_vrp_windows_do_not_overlap():
    records = []
    start = date(2025, 11, 10)
    for i in range(40):
        records.append(
            {
                "date": start + timedelta(days=i),
                "close": 100.0 * (1.001 ** i),
                "iv": 0.25,
                "trend_regime": "uptrend",
                "vol_regime": "low_vol",
            }
        )

    def always_long(_records, _index):
        return 1

    rows = variance_risk_observations(
        records,
        symbol="SPY",
        source="vendor_iv",
        study_start=start,
        study_end=records[-1]["date"],
        side_at=always_long,
        horizon=15,
    )
    assert [row["signal_date"] for row in rows] == [start, start + timedelta(days=15)]
    assert rows[0]["end_date"] == start + timedelta(days=15)
    assert rows[0]["iv_minus_rv"] == pytest.approx(rows[0]["iv"] - rows[0]["forward_rv"])


def test_stock_stop_time_exit_and_non_overlap():
    records = _flat(12)
    trades, skips = run_protected_trades(
        records,
        symbol="SPY",
        strategy="trend_continuation",
        side_at=lambda _records, index: 1 if index in (5, 6) else 0,
        max_hold=3,
        invalidated=lambda _bar, _side, _level: False,
        level_at=lambda _records, _index, _side: None,
        study_start=date(2020, 1, 1),
        study_end=date(2030, 1, 1),
    )
    assert skips == []
    assert len(trades) == 1
    trade = trades[0]
    assert trade["exit_reason"] == "time"
    assert trade["exit_index"] == 9
    entry = apply_slippage(100.0, 1, "entry")
    exit_fill = apply_slippage(100.0, 1, "exit")
    assert trade["pnl"] == pytest.approx((exit_fill - entry) * trade["shares"])
    assert trade["r_multiple"] < 0


def test_gap_stop_fills_at_the_open():
    records = _flat(10)
    records[7]["open"] = 90.0
    records[7]["low"] = 89.0
    trades, _skips = run_protected_trades(
        records,
        symbol="SPY",
        strategy="trend_continuation",
        side_at=lambda _records, index: 1 if index == 5 else 0,
        max_hold=10,
        invalidated=lambda _bar, _side, _level: False,
        level_at=lambda _records, _index, _side: None,
        study_start=date(2020, 1, 1),
        study_end=date(2030, 1, 1),
    )
    assert trades[0]["exit_reason"] == "gap_stop"
    assert trades[0]["exit_price"] == pytest.approx(apply_slippage(90.0, 1, "exit"))
    assert trades[0]["r_multiple"] < -1


def test_signal_on_the_last_bar_does_not_invent_an_entry():
    records = _flat(6)
    trades, _skips = run_protected_trades(
        records,
        symbol="SPY",
        strategy="trend_continuation",
        side_at=lambda _records, index: 1 if index == len(records) - 1 else 0,
        max_hold=3,
        invalidated=lambda _bar, _side, _level: False,
        level_at=lambda _records, _index, _side: None,
        study_start=date(2020, 1, 1),
        study_end=date(2030, 1, 1),
    )
    assert trades == []


def _flat(n: int, price: float = 100.0):
    rows = []
    start = date(2026, 1, 1)
    for i in range(n):
        rows.append(
            {
                "date": start + timedelta(days=i),
                "open": price,
                "high": price + 0.5,
                "low": price - 0.5,
                "close": price,
                "atr14": 2.0,
                "trend_regime": "uptrend",
                "vol_regime": "low_vol",
                "iv": None,
                "rv20": None,
                "iv_pct": None,
            }
        )
    return rows
