"""The live page's JavaScript must compute the stretch pattern exactly like the backtest."""

import json
import math
import shutil
import subprocess
from datetime import date, timedelta
from pathlib import Path

import pytest

from oppfinder.features import build_records
from oppfinder.signals import mean_reversion_side

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which("node")
pytestmark = pytest.mark.skipif(NODE is None, reason="node is not installed")


def _js(closes_list: list[list[float]]) -> list[dict]:
    script = (
        "import { lastBarIndicators, stretchSide } from './ui/core/market.mjs';"
        "const input = JSON.parse(process.argv[1]);"
        "console.log(JSON.stringify(input.map((c) => { const i = lastBarIndicators(c); return { ...i, side: stretchSide(i) }; })));"
    )
    done = subprocess.run(
        [NODE, "--input-type=module", "-e", script, json.dumps(closes_list)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(done.stdout)


def _bars(closes: list[float]) -> list[dict]:
    start = date(2025, 1, 1)
    return [
        {"date": start + timedelta(days=i), "open": c, "high": c, "low": c, "close": c, "volume": 1.0}
        for i, c in enumerate(closes)
    ]


def _python(closes: list[float]) -> dict:
    records = build_records(_bars(closes))
    last = records[-1]
    return {
        "sma20": last["sma20"],
        "sma200": last["sma200"],
        "std20": last["std20"],
        "rsi2": last["rsi2"],
        "rv20": last["rv20"],
        "side": mean_reversion_side(records, len(records) - 1),
    }


def _cached(symbol: str) -> list[float]:
    payload = json.loads((ROOT / "data" / "prices" / f"{symbol}.json").read_text())
    return [float(bar["close"]) for bar in payload["bars"] if bar["date"] <= "2026-11-10"]


def _series() -> list[list[float]]:
    out = []
    for symbol in ("SPY", "NBIS"):
        closes = _cached(symbol)
        for cut in (len(closes), len(closes) - 40, len(closes) - 120):
            out.append(closes[:cut])
    rise = [100 * math.exp(0.002 * i) for i in range(260)]
    out.append(rise + [rise[-1] * 0.97, rise[-1] * 0.93])
    fall = [100 * math.exp(-0.002 * i) for i in range(260)]
    out.append(fall + [fall[-1] * 1.03, fall[-1] * 1.07])
    return out


def test_js_indicators_match_python_backtest():
    series = _series()
    js_rows = _js(series)
    for closes, js in zip(series, js_rows):
        py = _python(closes)
        for key in ("sma20", "sma200", "std20", "rsi2", "rv20"):
            assert js[key] == pytest.approx(py[key], rel=1e-9, abs=1e-9), key
        assert js["side"] == py["side"]


def test_synthetic_stretches_fire_both_ways():
    series = _series()
    js_rows = _js(series[-2:])
    assert js_rows[0]["side"] == 1
    assert js_rows[1]["side"] == -1


def test_node_unit_tests_pass():
    done = subprocess.run([NODE, "--test", "ui/tests/market.test.mjs"], cwd=ROOT, capture_output=True, text=True)
    assert done.returncode == 0, done.stdout + done.stderr
