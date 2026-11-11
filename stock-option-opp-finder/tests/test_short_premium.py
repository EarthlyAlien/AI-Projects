from datetime import date, timedelta
from decimal import Decimal

import pytest

from oppfinder.short_premium import backtest_short_credit, premium_windows, summarize_premium_windows
from oppfinder.spreads import ChainRow


def _records(closes: list[float]):
    start = date(2026, 1, 1)
    return [
        {
            "date": start + timedelta(days=i),
            "close": price,
            "raw_close": price,
            "open": price,
            "high": price + 1,
            "low": price - 1,
            "trend_regime": "uptrend",
            "vol_regime": "low_vol",
            "iv": 0.20,
            "rv20": 0.15,
            "iv_pct": 0.9,
        }
        for i, price in enumerate(closes)
    ]


_EXPIRATION = date(2026, 1, 21)


def _leg(day: date, strike: str, bid: str, ask: str, delta: str) -> ChainRow:
    return ChainRow(
        expiration=_EXPIRATION,
        strike=Decimal(strike),
        call_put="PUT",
        bid=Decimal(bid),
        ask=Decimal(ask),
        iv=Decimal("0.2"),
        delta=Decimal(delta),
    )


def _getter(entry_exit: dict[date, list[ChainRow]]):
    def get(_symbol: str, day: date):
        rows = entry_exit.get(day)
        if rows is None:
            return "empty", []
        return "ok", rows

    return get


def _bullish(_records, index):
    return 1 if index == 0 else 0


def test_one_session_credit_vertical_pnl():
    records = _records([110.0, 110.0, 112.0])
    entry_day, exit_day = records[1]["date"], records[2]["date"]
    getter = _getter(
        {
            entry_day: [
                _leg(entry_day, "100", "2.00", "2.10", "-0.30"),
                _leg(entry_day, "95", "0.70", "0.80", "-0.20"),
            ],
            exit_day: [
                _leg(exit_day, "100", "0.45", "0.50", "-0.10"),
                _leg(exit_day, "95", "0.18", "0.22", "-0.05"),
            ],
        }
    )
    trades, skips, unmarked = backtest_short_credit(
        records,
        "TEST",
        "custom",
        1,
        False,
        (14, 5, 25),
        getter,
        [],
        records[0]["date"],
        records[-1]["date"],
        side_at=_bullish,
    )
    assert skips == []
    assert unmarked == []
    assert len(trades) == 1
    # credit 2.00 - 0.80 = 1.20; exit debit 0.50 - 0.18 = 0.32; 2 contracts
    assert trades[0]["premium"] == Decimal("1.20")
    assert trades[0]["pnl"] == pytest.approx((1.20 - 0.32) * 200 - 5.20)
    assert trades[0]["exit_reason"] == "time"


def test_profit_target_closes_on_first_mark():
    records = _records([110.0, 110.0, 111.0, 90.0])
    entry_day, day1 = records[1]["date"], records[2]["date"]
    getter = _getter(
        {
            entry_day: [
                _leg(entry_day, "100", "2.00", "2.10", "-0.30"),
                _leg(entry_day, "95", "0.70", "0.80", "-0.20"),
            ],
            day1: [
                _leg(day1, "100", "0.45", "0.50", "-0.10"),
                _leg(day1, "95", "0.18", "0.22", "-0.05"),
            ],
        }
    )
    trades, _skips, unmarked = backtest_short_credit(
        records,
        "TEST",
        "custom",
        2,
        True,
        (14, 5, 25),
        getter,
        [],
        records[0]["date"],
        records[-1]["date"],
        side_at=_bullish,
    )
    assert unmarked == []
    assert trades[0]["exit_reason"] == "profit_target"
    assert trades[0]["exit_date"] == day1


def test_missing_exit_quote_is_unmarked_not_modeled():
    records = _records([110.0, 110.0, 112.0])
    entry_day = records[1]["date"]
    getter = _getter(
        {
            entry_day: [
                _leg(entry_day, "100", "2.00", "2.10", "-0.30"),
                _leg(entry_day, "95", "0.70", "0.80", "-0.20"),
            ]
        }
    )
    trades, _skips, unmarked = backtest_short_credit(
        records,
        "TEST",
        "custom",
        1,
        False,
        (14, 5, 25),
        getter,
        [],
        records[0]["date"],
        records[-1]["date"],
        side_at=_bullish,
    )
    assert trades == []
    assert len(unmarked) == 1
    assert unmarked[0]["reason"] == "exit_quote_missing"


def test_premium_window_breach_uses_signal_iv():
    records = _records([100.0, 90.0])
    rows = premium_windows(
        records,
        "TEST",
        "custom",
        1,
        records[0]["date"],
        records[-1]["date"],
        side_at=_bullish,
    )
    assert len(rows) == 1
    # expected move = 0.20 * sqrt(1/252) = 1.26%; a 10% drop breaches it
    assert rows[0]["breach_close"] is True
    assert rows[0]["signed_return"] == pytest.approx(-0.10)
    summary = summarize_premium_windows(rows)
    assert summary["breach_close_rate"] == 1.0
    assert summary["mean_iv_minus_forward_rv"] is not None
