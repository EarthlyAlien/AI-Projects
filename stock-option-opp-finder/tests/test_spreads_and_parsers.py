from datetime import date
from decimal import Decimal

import pytest

from oppfinder.data_sources import (
    extract_cnn_fear_greed,
    extract_gdelt_tone,
    parse_cboe_index_csv,
    parse_put_call_csv,
    parse_yahoo_chart,
    subsequent_split_factor,
)
from oppfinder.data_sources import Split
from oppfinder.spreads import (
    ChainRow,
    adjacent_otm_strike,
    build_credit_vertical,
    build_debit_vertical,
    find_leg,
    option_pnl,
    pick_expiration,
    size_contracts,
    valid_quote,
)


def _row(strike, right, bid, ask, delta, expiration="2026-12-18"):
    return ChainRow(
        expiration=date.fromisoformat(expiration),
        strike=Decimal(strike),
        call_put=right,
        bid=Decimal(bid),
        ask=Decimal(ask),
        iv=Decimal("0.20"),
        delta=Decimal(delta),
    )


def test_expiration_tie_prefers_the_longer_listed_date():
    trade_date = date(2026, 11, 6)
    # 28 DTE and 42 DTE are equally far from a 35-day target.
    chosen = pick_expiration([date(2026, 12, 4), date(2026, 12, 18)], trade_date, 35, 21, 50)
    assert chosen == date(2026, 12, 18)


def test_put_credit_uses_the_next_lower_strike_from_the_real_spy_grid():
    rows = [
        _row("706", "PUT", "10.86", "10.98", "-0.2811"),
        _row("713", "PUT", "12.29", "12.42", "-0.3178"),
        _row("721", "PUT", "14.19", "14.33", "-0.3657"),
        _row("550", "PUT", "1.30", "1.34", "-0.0276"),
    ]
    spread, reason = build_credit_vertical(rows, Decimal("735.29"), date(2026, 11, 6), "PUT", (35, 25, 55))
    assert reason == "ok"
    assert spread is not None
    assert spread.short_strike == Decimal("713")
    assert spread.long_strike == Decimal("706")
    assert spread.premium == Decimal("1.31")
    assert spread.width == Decimal("7")
    assert spread.max_loss == Decimal("5.69")


def test_call_debit_uses_the_next_higher_strike():
    rows = [
        _row("743", "CALL", "16.64", "16.84", "0.4732"),
        _row("750", "CALL", "12.75", "12.91", "0.4099"),
        _row("765", "CALL", "6.28", "6.39", "0.2662"),
    ]
    spread, reason = build_debit_vertical(rows, date(2026, 11, 6), "CALL", (35, 21, 50))
    assert reason == "ok"
    assert spread is not None
    assert (spread.long_strike, spread.short_strike) == (Decimal("743"), Decimal("750"))
    assert spread.premium == Decimal("4.09")
    assert spread.max_profit == Decimal("2.91")


def test_bad_quotes_and_missing_exit_leg_are_rejected():
    assert valid_quote(_row("100", "CALL", "0", "0.10", "0.40")) is False
    assert valid_quote(_row("100", "CALL", "1.00", "2.00", "0.40")) is False
    rows = [_row("100", "CALL", "1.00", "1.05", "0.40"), _row("100", "CALL", "1.00", "1.05", "0.40")]
    assert find_leg(rows, date(2026, 12, 18), Decimal("100"), "CALL") is None
    assert adjacent_otm_strike([Decimal("10"), Decimal("12"), Decimal("15")], Decimal("12"), "CALL") == Decimal("15")
    assert adjacent_otm_strike([Decimal("10"), Decimal("12"), Decimal("15")], Decimal("12"), "PUT") == Decimal("10")


def test_option_pnl_and_contract_sizing():
    rows = [
        _row("706", "PUT", "10.86", "10.98", "-0.2811"),
        _row("713", "PUT", "12.29", "12.42", "-0.3178"),
    ]
    spread, _reason = build_credit_vertical(rows, Decimal("735"), date(2026, 11, 6), "PUT", (35, 25, 55))
    assert spread is not None
    pnl, commission = option_pnl(spread, Decimal("0.10"), Decimal("0.50"), 1)
    # Credit 1.31, pay 0.40 to close, $91 gross, $2.60 commission.
    assert pnl == Decimal("88.40")
    assert commission == Decimal("2.60")
    assert size_contracts(Decimal("5.69")) == 1
    assert size_contracts(Decimal("15")) == 1
    assert size_contracts(Decimal("30")) is None


def test_split_factor_restores_the_pre_split_price():
    splits = [Split(date(2025, 11, 17), 10, 1)]
    assert subsequent_split_factor(date(2025, 11, 14), splits) == 10
    assert subsequent_split_factor(date(2025, 11, 17), splits) == 1


def test_parsers_skip_junk_and_keep_real_rows():
    cboe = parse_cboe_index_csv("not a row\nDATE,OPEN,HIGH,LOW,CLOSE\n11/09/2026,25.08,25.08,19.64,19.92\n")
    assert cboe == [{"date": date(2026, 11, 9), "open": 25.08, "high": 25.08, "low": 19.64, "close": 19.92}]
    pc = parse_put_call_csv("disclaimer\nDATE,CALL,PUT,TOTAL,P/C Ratio\n10/04/2019,1,2,3,0.65\n")
    assert pc[-1]["date"] == date(2019, 10, 4)
    assert pc[-1]["put_call"] == pytest.approx(0.65)
    payload = {
        "chart": {
            "result": [
                {
                    "timestamp": [1790861400],
                    "indicators": {
                        "quote": [{"open": [10.0], "high": [11.0], "low": [9.0], "close": [10.5], "volume": [100]}]
                    },
                    "events": {"splits": {"1794321000": {"date": 1794321000, "numerator": 10, "denominator": 1}}},
                }
            ],
            "error": None,
        }
    }
    bars, splits = parse_yahoo_chart(payload)
    assert bars[0]["date"] == date(2026, 10, 1)
    assert bars[0]["raw_close"] == pytest.approx(105.0)
    assert splits[0].ex_date == date(2026, 11, 10)


def test_sentiment_extractors_reject_unknown_shapes():
    tone = extract_gdelt_tone(
        {"timeline": [{"data": [{"date": "20251110T120000Z", "value": -1.5}, {"date": "20251111T120000Z", "value": 0.25}]}]}
    )
    assert tone == [(date(2025, 11, 10), -1.5), (date(2025, 11, 11), 0.25)]
    assert extract_gdelt_tone({"timeline": [{"data": [{"score": 1}]}]}) is None
    fear = extract_cnn_fear_greed({"fear_and_greed_historical": {"data": [{"x": 1794321000000, "y": 42}]}})
    assert fear is not None and fear[0][1] == 42
    assert extract_cnn_fear_greed({"fear_and_greed": {"score": 10}}) is None
