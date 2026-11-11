import json
from datetime import date

from oppfinder.ui_data import price_series, window_rows


def test_price_series_keeps_study_window_only(tmp_path):
    path = tmp_path / "TEST.json"
    path.write_text(
        json.dumps(
            {
                "bars": [
                    {"date": "2025-11-09", "close": 90.0},
                    {"date": "2025-11-10", "close": 100.0},
                    {"date": "2026-11-10", "close": 110.0},
                    {"date": "2026-11-11", "close": 120.0},
                ],
                "splits": [],
            }
        )
    )
    rows = price_series(path, date(2025, 11, 10), date(2026, 11, 10))
    assert [row["close"] for row in rows] == [100.0, 110.0]


def test_window_rows_parse_booleans(tmp_path):
    path = tmp_path / "windows.csv"
    path.write_text(
        "symbol,family,horizon,signal_date,end_date,side,signed_return,adverse_close,adverse_intra,breach_close,breach_intra\n"
        "SPY,mr_fade,2,2026-01-05,2026-01-07,1,0.012,0.0,0.004,False,True\n"
    )
    rows = window_rows(path)
    assert rows[0]["horizon"] == 2
    assert rows[0]["breach_close"] is False
    assert rows[0]["breach_intra"] is True
    assert rows[0]["signed_return"] == 0.012
