"""Run the 1-3 session premium study for SPY and NBIS and write its outputs."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path

from oppfinder.config import STUDY_END, STUDY_START, WARMUP_START
from oppfinder.data_sources import ResearchStore
from oppfinder.features import build_records
from oppfinder.run import INDEXES, _last_complete
from oppfinder.short_premium import EXITS, FAMILIES, MONTHLY_DTE, NEAR_DTE, backtest_short_credit, premium_windows, summarize_premium_windows
from oppfinder.short_report import render_short
from oppfinder.stats import summarize

SYMBOLS = ("SPY", "NBIS")
DTES = (("near", NEAR_DTE), ("monthly", MONTHLY_DTE))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the 1-3 session SPY/NBIS premium study.")
    parser.add_argument("--output", type=Path, default=Path("output/spy-nbis-short"))
    parser.add_argument("--findings", type=Path, default=None)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    store = ResearchStore(root / "data", refresh=args.refresh)
    result = execute(store, root)
    output = args.output if args.output.is_absolute() else root / args.output
    output.mkdir(parents=True, exist_ok=True)
    _write_outputs(output, result)
    (output / "summary.md").write_text(render_short(result, frontmatter=False))
    if args.findings:
        args.findings.parent.mkdir(parents=True, exist_ok=True)
        args.findings.write_text(render_short(result, frontmatter=True))
    print(f"wrote {output / 'summary.md'}", flush=True)
    return 0 if result["frames_ready"] else 1


def execute(store: ResearchStore, root: Path) -> dict:
    prices: dict[str, list[dict]] = {}
    splits: dict[str, list] = {}
    indexes: dict[str, list[dict]] = {}
    for symbol in SYMBOLS:
        bars, symbol_splits = store.load_prices(symbol, WARMUP_START, STUDY_END)
        prices[symbol] = bars
        splits[symbol] = symbol_splits
        print(f"prices {symbol}: {len(bars)} bars", flush=True)
    for name in INDEXES:
        indexes[name] = store.load_index(name)
        print(f"index {name}: {len(indexes[name])} rows", flush=True)
    vols = store.load_volatility("SPY", WARMUP_START, STUDY_END)
    print(f"iv SPY: {len(vols)} rows", flush=True)
    last_complete, _rule = _last_complete(prices, indexes)
    print(f"last complete session {last_complete.isoformat()}", flush=True)
    frames: dict[str, list[dict]] = {}
    split_dates: dict[str, list[date]] = {}
    for symbol in SYMBOLS:
        bars = [bar for bar in prices.get(symbol, []) if bar["date"] <= last_complete]
        if not bars:
            continue
        points = []
        if symbol == "SPY":
            points = [
                (row["date"], float(row["iv_current"]))
                for row in vols
                if row.get("iv_current") is not None and row["date"] <= last_complete
            ]
        frames[symbol] = build_records(bars, points)
        split_dates[symbol] = [split.ex_date for split in splits.get(symbol, [])]

    variants: list[dict] = []
    all_trades: list[dict] = []
    all_unmarked: list[dict] = []
    attempted = 0
    marked = 0
    spy = frames.get("SPY") or []
    for family in FAMILIES:
        for exit_label, hold, target in EXITS:
            for dte_label, dte in DTES:
                trades, skips, unmarked = backtest_short_credit(
                    spy,
                    "SPY",
                    family,
                    hold,
                    target,
                    dte,
                    store.load_chain,
                    split_dates.get("SPY", []),
                    STUDY_START,
                    last_complete,
                )
                variant = f"{family}_{exit_label}_{dte_label}"
                core = summarize(trades)
                variants.append(
                    {
                        "variant": variant,
                        "family": family,
                        "exit": exit_label,
                        "dte": dte_label,
                        "unmarked_n": len(unmarked),
                        "skip_counts": _count(skips),
                        **core,
                    }
                )
                all_trades.extend(trades)
                all_unmarked.extend(unmarked)
                marked += len(trades)
                attempted += len(trades) + len(unmarked)
                print(f"{variant}: marked {len(trades)} unmarked {len(unmarked)}", flush=True)

    window_rows: list[dict] = []
    window_summaries: list[dict] = []
    for symbol, records in frames.items():
        for family in FAMILIES:
            for horizon in (1, 2, 3):
                windows = premium_windows(records, symbol, family, horizon, STUDY_START, last_complete)
                window_rows.extend(windows)
                window_summaries.append(
                    {"symbol": symbol, "family": family, "horizon": horizon, **summarize_premium_windows(windows)}
                )
    ranked = sorted(
        [row for row in window_summaries if row["n"] > 0],
        key=lambda row: (
            row.get("breach_close_rate") if row.get("breach_close_rate") is not None else 1.0,
            -(row.get("mean_signed_return") or 0.0),
        ),
    )
    current_signals = []
    for symbol, records in frames.items():
        if not records or records[-1]["date"] != last_complete:
            continue
        index = len(records) - 1
        for family, side_fn in FAMILIES.items():
            side = side_fn(records, index)
            if side != 0:
                current_signals.append({"symbol": symbol, "family": family, "side": side})
    snapshot = _load_snapshot(root)
    return {
        "first_session": STUDY_START.isoformat(),
        "last_complete": last_complete.isoformat(),
        "frames_ready": bool(frames),
        "variants": variants,
        "direct_summary": {"attempted": attempted, "marked": marked, "unmarked": attempted - marked},
        "window_summaries": window_summaries,
        "window_rows": window_rows,
        "ranked_candidates": ranked,
        "candidate": ranked[0] if ranked else None,
        "current_signals": current_signals,
        "snapshot": snapshot,
        "illustrations": _illustrations(snapshot),
        "trades": all_trades,
        "unmarked": all_unmarked,
        "chain_counts": dict(store.chain_counts),
        "errors": list(store.errors),
    }


def _illustrations(snapshot: dict | None) -> list[dict]:
    if not snapshot:
        return []
    out = []
    quotes = snapshot.get("put_quotes") or []
    for symbol in ("SPY", "NBIS"):
        legs = sorted(
            [q for q in quotes if q["symbol"] == symbol],
            key=lambda q: float(q["strike"]),
            reverse=True,
        )
        shorts = [
            (abs(abs(float(q["delta"])) - 0.30), pos)
            for pos, q in enumerate(legs)
            if q.get("delta") is not None
        ]
        if not shorts:
            continue
        start = min(shorts)[1]
        for upper, lower in zip(legs[start:], legs[start + 1 :]):
            credit = float(upper["bid"]) - float(lower["ask"])
            width = float(upper["strike"]) - float(lower["strike"])
            if credit <= 0 or width <= 0:
                continue
            out.append(
                {
                    "symbol": symbol,
                    "expiration": upper["expiration"],
                    "short_strike": float(upper["strike"]),
                    "long_strike": float(lower["strike"]),
                    "short_bid": float(upper["bid"]),
                    "long_ask": float(lower["ask"]),
                    "credit": credit,
                    "width": width,
                    "max_loss_dollars": (width - credit) * 100,
                }
            )
            break
    return out


def _load_snapshot(root: Path) -> dict | None:
    path = root / "data" / "current_snapshot_2026-11-11.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _count(skips: list[dict]) -> dict:
    counts: dict[str, int] = {}
    for skip in skips:
        counts[skip["reason"]] = counts.get(skip["reason"], 0) + 1
    return counts


def _write_outputs(output: Path, result: dict) -> None:
    trade_fields = [
        "result_type", "strategy", "family", "symbol", "side", "status", "signal_date", "entry_date", "exit_date",
        "exit_reason", "structure", "expiration", "long_strike", "short_strike", "premium", "width", "contracts",
        "max_loss", "risk_dollars", "commissions", "pnl", "r_multiple", "underlying_return",
    ]
    with (output / "trades.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=trade_fields, extrasaction="ignore")
        writer.writeheader()
        for trade in result["trades"]:
            writer.writerow({field: _cell(trade.get(field)) for field in trade_fields})
    window_fields = [
        "symbol", "family", "horizon", "signal_date", "end_date", "side", "raw_return", "signed_return",
        "adverse_close", "adverse_intra", "expected_move", "expected_move_source", "breach_close", "breach_intra",
        "inside_close", "iv", "forward_rv", "iv_minus_forward_rv",
    ]
    with (output / "windows.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=window_fields, extrasaction="ignore")
        writer.writeheader()
        for row in result["window_rows"]:
            writer.writerow({field: _cell(row.get(field)) for field in window_fields})
    payload = {key: value for key, value in result.items() if key not in ("trades", "window_rows", "unmarked")}
    (output / "stats.json").write_text(json.dumps(payload, indent=2, default=_default))
    (output / "unmarked.csv").write_text(
        "variant,symbol,signal_date,entry_date,intended_exit,underlying_return\n"
        + "\n".join(
            f"{row['strategy']},{row['symbol']},{row['signal_date']},{row['entry_date']},{row['intended_exit']},{row['underlying_return']:.6f}"
            for row in result["unmarked"]
        )
        + "\n"
    )


def _cell(value):
    if value is None:
        return ""
    if isinstance(value, date):
        return value.isoformat()
    return value


def _default(value):
    if isinstance(value, date):
        return value.isoformat()
    raise TypeError(type(value))


if __name__ == "__main__":
    sys.exit(main())
