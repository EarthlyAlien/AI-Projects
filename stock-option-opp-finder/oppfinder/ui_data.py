"""Build the static UI data file from checked-in run outputs. No network."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path

STUDY_START = date(2025, 11, 10)
STUDY_END = date(2026, 11, 10)


def price_series(path: Path, start: date = STUDY_START, end: date = STUDY_END) -> list[dict]:
    """Daily closes for one symbol from a cached Yahoo price file, study window only."""
    payload = json.loads(path.read_text())
    rows = []
    for bar in payload.get("bars") or []:
        day = date.fromisoformat(str(bar["date"])[:10])
        if start <= day <= end:
            rows.append({"date": day.isoformat(), "close": float(bar["close"])})
    return rows


def window_rows(path: Path) -> list[dict]:
    rows = []
    with path.open() as handle:
        for row in csv.DictReader(handle):
            rows.append(
                {
                    "symbol": row["symbol"],
                    "family": row["family"],
                    "horizon": int(row["horizon"]),
                    "signal_date": row["signal_date"],
                    "end_date": row["end_date"],
                    "side": int(row["side"]),
                    "signed_return": float(row["signed_return"]),
                    "adverse_close": float(row["adverse_close"]),
                    "adverse_intra": float(row["adverse_intra"]),
                    "breach_close": row["breach_close"] == "True",
                    "breach_intra": row["breach_intra"] == "True",
                }
            )
    return rows


def build_data(root: Path) -> dict:
    main = _json(root / "output" / "stats.json")
    pair = _json(root / "output" / "spy-nbis" / "stats.json")
    short = _json(root / "output" / "spy-nbis-short" / "stats.json")
    prices = {
        symbol: price_series(root / "data" / "prices" / f"{symbol}.json")
        for symbol in ("SPY", "NBIS")
    }
    return {
        "generated_from": "checked-in outputs under output/; no live data",
        "study": {"start": STUDY_START.isoformat(), "end": STUDY_END.isoformat()},
        "main_summaries": main.get("summaries") or [],
        "headline_option": main.get("headline_option"),
        "headline_proxy": main.get("headline_proxy"),
        "pair_paths": pair.get("paths") or [],
        "pair_link": pair.get("link") or {},
        "by_symbol": pair.get("by_symbol") or [],
        "variants": short.get("variants") or [],
        "direct_summary": short.get("direct_summary") or {},
        "window_summaries": short.get("window_summaries") or [],
        "ranked_candidates": short.get("ranked_candidates") or [],
        "windows": window_rows(root / "output" / "spy-nbis-short" / "windows.csv"),
        "illustrations": short.get("illustrations") or [],
        "snapshot": short.get("snapshot"),
        "prices": prices,
        "current_signals": short.get("current_signals") or [],
        "last_complete": short.get("last_complete"),
    }


def _json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build ui/data.json from checked-in outputs.")
    parser.add_argument("--out", type=Path, default=Path("ui/data.json"))
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    out = args.out if args.out.is_absolute() else root / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(build_data(root), indent=1))
    print(f"wrote {out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
