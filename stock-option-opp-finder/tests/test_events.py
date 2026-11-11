from datetime import date, timedelta

import pytest

from oppfinder.events import linked_returns, path_summary, signal_windows, summarize_windows
from oppfinder.features import build_records
from oppfinder.run import _events


def _bars(closes: list[float]):
    start = date(2026, 1, 1)
    return [{"date": start + timedelta(days=i), "close": price, "volume": 1000.0} for i, price in enumerate(closes)]


def _always_long(_records, _index):
    return 1


def _flat(_records, _index):
    return 0


def test_forward_window_uses_the_close_horizon_sessions_later():
    records = _bars([100, 100, 110, 121])
    rows = signal_windows(
        records,
        lambda _records, index: 1 if index == 0 else 0,
        2,
        date(2026, 1, 1),
        date(2026, 1, 4),
        overlap="overlapping",
    )
    assert len(rows) == 1
    assert rows[0]["end_date"] == date(2026, 1, 3)
    assert rows[0]["raw_return"] == pytest.approx(0.10)
    assert rows[0]["signed_return"] == pytest.approx(0.10)


def test_short_sign_flips_the_return():
    records = _bars([100, 90])
    rows = signal_windows(
        records,
        lambda _records, index: -1 if index == 0 else 0,
        1,
        date(2026, 1, 1),
        date(2026, 1, 2),
        overlap="overlapping",
    )
    assert rows[0]["raw_return"] == pytest.approx(-0.10)
    assert rows[0]["signed_return"] == pytest.approx(0.10)


def test_incomplete_window_is_omitted():
    records = _bars([100, 110, 120])
    rows = signal_windows(records, _always_long, 5, date(2026, 1, 1), date(2026, 1, 10), overlap="overlapping")
    assert rows == []


def test_non_overlapping_windows_do_not_share_interior_bars():
    records = _bars([100 + i for i in range(20)])
    rows = signal_windows(records, _always_long, 5, date(2026, 1, 1), date(2026, 2, 1), overlap="non_overlapping")
    assert [row["signal_index"] for row in rows] == [0, 5, 10]
    assert rows[0]["end_index"] == 5
    assert rows[1]["signal_index"] == 5


def test_flat_signal_produces_no_rows():
    records = _bars([100, 110, 120, 130])
    assert signal_windows(records, _flat, 1, date(2026, 1, 1), date(2026, 2, 1), overlap="overlapping") == []


def test_small_event_sample_is_not_supported():
    records = _bars([100, 110, 120, 130])
    rows = signal_windows(records, _always_long, 1, date(2026, 1, 1), date(2026, 2, 1), overlap="non_overlapping")
    summary = summarize_windows(rows)
    assert summary["n"] < 30
    assert summary["evidence"] == "too_small"


def test_path_drawdown_and_return():
    records = _bars([100, 120, 90, 90])
    summary = path_summary(records, date(2026, 1, 1), date(2026, 1, 4))
    assert summary["simple_return"] == pytest.approx(-0.10)
    assert summary["max_drawdown"] == pytest.approx(0.25)
    assert summary["sessions"] == 4
    assert summary["avg_dollar_volume"] == pytest.approx((100 + 120 + 90 + 90) * 1000 / 4)


def test_overlapping_summary_is_not_a_significance_claim():
    start = date(2025, 1, 1)
    bars = []
    price = 100.0
    for i in range(80):
        price *= 1.001
        bars.append(
            {
                "date": start + timedelta(days=i),
                "open": price,
                "high": price + 1,
                "low": price - 1,
                "close": price,
                "volume": 2_000_000,
                "raw_close": price,
            }
        )
    _rows, summaries = _events({"TEST": build_records(bars)}, start + timedelta(days=79))
    overlapping = [row for row in summaries if row["overlap"] == "overlapping"]
    assert overlapping
    assert {row["evidence"] for row in overlapping} == {"overlapping"}


def test_beta_of_a_two_for_one_path():
    left_closes = [100.0]
    right_closes = [50.0]
    for left_return, right_return in ((0.01, 0.02), (0.02, 0.04), (-0.01, -0.02), (0.03, 0.06)):
        left_closes.append(left_closes[-1] * (1 + left_return))
        right_closes.append(right_closes[-1] * (1 + right_return))
    link = linked_returns(_bars(left_closes), _bars(right_closes), date(2026, 1, 2), date(2026, 1, 6))
    assert link["n"] == 4
    assert link["correlation"] == pytest.approx(1.0)
    assert link["beta"] == pytest.approx(2.0)
