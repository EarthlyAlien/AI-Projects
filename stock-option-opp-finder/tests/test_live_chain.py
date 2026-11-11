from datetime import date

import pytest

from oppfinder.live_chain import build_credit_candidate, parse_cboe_chain, parse_occ, pattern_checks, pick_expiry


def test_parse_occ_with_prefix():
    assert parse_occ("B1SPY261113C00710000") == (date(2026, 11, 13), "CALL", 710.0)
    assert parse_occ("NBIS261113P00140000") == (date(2026, 11, 13), "PUT", 140.0)
    assert parse_occ("junk") is None


def test_pick_expiry_skips_today():
    assert pick_expiry(["2026-11-11", "2026-11-12", "2026-11-13"], date(2026, 11, 11)) == "2026-11-12"


def _option(strike, bid, ask, delta):
    return {
        "expiration": "2026-11-13",
        "type": "PUT",
        "strike": strike,
        "bid": bid,
        "ask": ask,
        "iv": 0.2,
        "delta": delta,
        "open_interest": 100.0,
        "volume": 10.0,
    }


def test_put_credit_candidate_math():
    options = [_option(100.0, 2.0, 2.1, -0.30), _option(95.0, 0.7, 0.8, -0.20), _option(90.0, 0.3, 0.4, -0.12)]
    candidate = build_credit_candidate(options, "2026-11-13", "PUT")
    assert candidate["short_strike"] == 100.0
    assert candidate["long_strike"] == 95.0
    assert candidate["credit"] == pytest.approx(1.2)
    assert candidate["max_loss_dollars"] == pytest.approx(380.0)
    assert candidate["breakeven"] == pytest.approx(98.8)


def test_candidate_uses_about_five_point_wing_on_dense_chain():
    options = [_option(float(strike), 2.0, 2.1, -0.30) for strike in (100, 99, 98, 97, 96, 95)]
    options[0] = _option(100.0, 3.0, 3.1, -0.30)
    candidate = build_credit_candidate(options, "2026-11-13", "PUT")
    assert candidate["long_strike"] == 95.0
    assert candidate["width"] == pytest.approx(5.0)


def test_checks_explain_in_plain_words():
    context = {"rv20": 0.15, "sma50": 90.0, "signals": {"mr_fade": 1}}
    candidate = build_credit_candidate(
        [_option(100.0, 2.0, 2.1, -0.30), _option(95.0, 0.7, 0.8, -0.20)],
        "2026-11-13",
        "PUT",
    )
    checks = pattern_checks(context, candidate, 20.0, 110.0)
    by_id = {check["id"]: check for check in checks}
    assert by_id["expensive"]["pass"] is True
    assert by_id["stretched"]["pass"] is True
    assert by_id["risk"]["pass"] is True
    assert "Worst case" in by_id["risk"]["detail"]


def test_parse_chain_keeps_underlying():
    payload = {
        "timestamp": "2026-11-11 16:29:09",
        "data": {
            "current_price": 100.0,
            "price_change_percent": 1.5,
            "prev_day_close": 98.0,
            "iv30": 20.0,
            "options": [
                {"option": "SPY261113P00100000", "bid": 1.0, "ask": 1.1, "iv": 0.2, "delta": -0.3, "open_interest": 5, "volume": 2}
            ],
        },
    }
    chain = parse_cboe_chain(payload, "SPY")
    assert chain["current_price"] == 100.0
    assert chain["expirations"] == ["2026-11-13"]
    assert chain["options"][0]["strike"] == 100.0
