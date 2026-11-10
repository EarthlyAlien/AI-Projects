"""Download public data, run the books, and write the checked-in outputs."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

from oppfinder.config import (
    BREAKOUT_HOLD,
    EQUITY0,
    IV_PCT_WINDOW,
    OPTION_SYMBOLS,
    PREMIUM_HOLD,
    PRICE_SYMBOLS,
    STUDY_END,
    STUDY_START,
    TREND_HOLD,
    MR_HOLD,
    WARMUP_START,
)
from oppfinder.data_sources import ResearchStore, probe_sentiment
from oppfinder.engine import run_protected_trades
from oppfinder.features import build_records, with_external_iv
from oppfinder.options_backtest import price_directional, price_premium
from oppfinder.report import render_findings
from oppfinder.scan import build_scan
from oppfinder.sentiment import mask_side
from oppfinder.signals import (
    BREAKOUT,
    MEAN_REVERSION,
    PREMIUM,
    TREND,
    breakout_invalid,
    breakout_level,
    breakout_side,
    mean_reversion_invalid,
    mean_reversion_side,
    no_level,
    premium_side,
    trend_invalid,
    trend_side,
)
from oppfinder.stats import pearson, select_headline, summarize
from oppfinder.vrp import summarize_vrp, variance_risk_observations

NY = ZoneInfo("America/New_York")
INDEXES = ("VIX", "VXN", "RVX", "VIX3M")
SPECS = (
    (TREND, trend_side, TREND_HOLD, trend_invalid, no_level),
    (MEAN_REVERSION, mean_reversion_side, MR_HOLD, mean_reversion_invalid, no_level),
    (BREAKOUT, breakout_side, BREAKOUT_HOLD, breakout_invalid, breakout_level),
)
_ORDER = {TREND: 0, MEAN_REVERSION: 1, PREMIUM: 2, BREAKOUT: 3}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the stock and listed-vertical research book.")
    parser.add_argument("--refresh", action="store_true", help="Ignore cached downloads.")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--findings", type=Path, default=None, help="Also write the report to this path.")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    store = ResearchStore(root / "data", refresh=args.refresh)
    result = execute(store, workers=args.workers)
    output = root / "output"
    output.mkdir(parents=True, exist_ok=True)
    _write_outputs(output, result)
    summary = render_findings(result, frontmatter=False)
    (output / "summary.md").write_text(summary)
    if args.findings:
        args.findings.parent.mkdir(parents=True, exist_ok=True)
        args.findings.write_text(render_findings(result, frontmatter=True))
    print(f"wrote {output / 'summary.md'}", flush=True)
    return 0 if result["backdrop"]["priced_symbols"] else 1


def execute(store: ResearchStore, workers: int = 4) -> dict:
    print("downloading prices, CBOE indexes, vendor IV, and sentiment probes", flush=True)
    prices, splits, vols, indexes, probe = _download(store, workers)
    last_complete, session_bits = _last_complete(prices, indexes)
    print(f"last complete session {last_complete.isoformat()}", flush=True)
    frames: dict[str, list[dict]] = {}
    split_dates: dict[str, list[date]] = {}
    diagnostics = []
    for symbol in PRICE_SYMBOLS:
        bars = [bar for bar in prices.get(symbol, []) if bar["date"] <= last_complete]
        if not bars:
            continue
        iv_points = [
            (row["date"], float(row["iv_current"]))
            for row in vols.get(symbol, [])
            if row.get("iv_current") is not None and row["date"] <= last_complete
        ]
        frames[symbol] = build_records(bars, iv_points)
        split_dates[symbol] = [split.ex_date for split in splits.get(symbol, [])]
        study_days = [row for row in frames[symbol] if STUDY_START <= row["date"] <= last_complete]
        diagnostics.append(
            {
                "symbol": symbol,
                "bars": len(frames[symbol]),
                "first": frames[symbol][0]["date"].isoformat(),
                "last": frames[symbol][-1]["date"].isoformat(),
                "study_days": len(study_days),
                "iv_points": len(iv_points),
                "iv_pct_study_days": sum(1 for row in study_days if row.get("iv_pct") is not None),
                "splits": [
                    {
                        "symbol": symbol,
                        "ex_date": split.ex_date.isoformat(),
                        "numerator": split.numerator,
                        "denominator": split.denominator,
                    }
                    for split in splits.get(symbol, [])
                ],
            }
        )
    underlying, underlying_skips = _run_underlying(frames, None)
    print(f"underlying trades {len(underlying)}", flush=True)
    option_trades, option_skips, unmarked = _run_options(
        frames, split_dates, underlying, store, workers, premium_side, last_complete
    )
    print(f"option trades {len(option_trades)} unmarked {len(unmarked)}", flush=True)
    vrp_rows = _vrp_rows(frames, indexes, last_complete)
    sentiment = _apply_sentiment(probe, frames, split_dates, store, workers, last_complete)
    trades = underlying + option_trades
    summaries = _summaries(trades)
    filtered_summaries = _summaries(sentiment["trades"]) if sentiment["applied"] else []
    scan = build_scan(frames, summaries, store.load_chain, last_complete) if frames else []
    backdrop = _backdrop(frames, indexes, diagnostics, last_complete, session_bits, prices)
    result = {
        "backdrop": backdrop,
        "summaries": summaries,
        "headline_option": select_headline(summaries, "direct_option"),
        "headline_proxy": select_headline(summaries, "underlying_proxy"),
        "vrp_summaries": [
            {"label": "Vendor IV on names with a chain history", "summary": summarize_vrp([row for row in vrp_rows if row["result_type"] == "vendor_iv"])},
            {"label": "VXN for QQQ and RVX for IWM, divided by 100 (index proxy, not a fill)", "summary": summarize_vrp([row for row in vrp_rows if row["result_type"] == "index_iv_proxy"])},
        ],
        "scan": scan,
        "skip_counts": _count(underlying_skips + option_skips),
        "unmarked_compare": _compare_unmarked(option_trades, unmarked),
        "sentiment": {
            "attempts": probe.get("attempts") or [],
            "applied": sentiment["applied"],
            "kind": sentiment.get("kind"),
            "label": sentiment.get("label"),
            "coverage": sentiment.get("coverage"),
            "filtered_summaries": filtered_summaries,
        },
        "chain_counts": dict(store.chain_counts),
        "errors": list(store.errors),
        "trades": trades + sentiment["trades"],
        "vrp_rows": vrp_rows,
        "unmarked": unmarked,
        "diagnostics": diagnostics,
    }
    _write_cached_tables(store.root, frames, vols, indexes, splits)
    return result


def _download(store: ResearchStore, workers: int):
    prices: dict[str, list[dict]] = {}
    splits: dict[str, list] = {}
    vols: dict[str, list[dict]] = {}
    indexes: dict[str, list[dict]] = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        price_futs = {pool.submit(store.load_prices, symbol, WARMUP_START, STUDY_END): symbol for symbol in PRICE_SYMBOLS}
        index_futs = {pool.submit(store.load_index, name): name for name in INDEXES}
        vol_futs = {pool.submit(store.load_volatility, symbol, WARMUP_START, STUDY_END): symbol for symbol in OPTION_SYMBOLS}
        probe_fut = pool.submit(probe_sentiment)
        for fut in as_completed(price_futs):
            symbol = price_futs[fut]
            try:
                bars, symbol_splits = fut.result()
            except Exception as exc:
                store.note("yahoo", f"{type(exc).__name__}: {exc}", symbol)
                bars, symbol_splits = [], []
            prices[symbol] = bars
            splits[symbol] = symbol_splits
            print(f"prices {symbol}: {len(bars)} bars, {len(symbol_splits)} splits", flush=True)
        for fut in as_completed(index_futs):
            name = index_futs[fut]
            try:
                indexes[name] = fut.result()
            except Exception as exc:
                store.note("cboe", f"{type(exc).__name__}: {exc}", name)
                indexes[name] = []
            print(f"index {name}: {len(indexes[name])} rows", flush=True)
        for fut in as_completed(vol_futs):
            symbol = vol_futs[fut]
            try:
                vols[symbol] = fut.result()
            except Exception as exc:
                store.note("dolthub_vol", f"{type(exc).__name__}: {exc}", symbol)
                vols[symbol] = []
            print(f"iv {symbol}: {len(vols[symbol])} rows", flush=True)
        try:
            probe = probe_fut.result()
        except Exception as exc:
            store.note("sentiment", f"{type(exc).__name__}: {exc}")
            probe = {"attempts": [{"source": "sentiment probe", "result": f"{type(exc).__name__}: {exc}"}], "gdelt": None, "cnn": None, "equity_put_call": []}
    return prices, splits, vols, indexes, probe


def _last_complete(prices: dict, indexes: dict) -> tuple[date, str]:
    candidates = [STUDY_END]
    bits = [f"requested end {STUDY_END.isoformat()}"]
    vix = indexes.get("VIX") or []
    spy = prices.get("SPY") or []
    if vix:
        candidates.append(vix[-1]["date"])
        bits.append(f"VIX file ends {vix[-1]['date'].isoformat()}")
    else:
        bits.append("VIX file missing, so the last price session was not confirmed by CBOE")
    if spy:
        candidates.append(spy[-1]["date"])
        bits.append(f"SPY download ends {spy[-1]['date'].isoformat()}")
    last = min(candidates)
    now = datetime.now(NY)
    if last == now.date() and now.hour < 16:
        last = last - timedelta(days=1)
        bits.append("dropped the New York session still in progress at download time")
    bits.append(f"study sessions run through {last.isoformat()}")
    return last, " ".join(bits)


def _run_underlying(frames: dict[str, list[dict]], overrides: dict | None):
    trades: list[dict] = []
    skips: list[dict] = []
    for symbol, records in frames.items():
        for name, side_fn, hold, invalid, level_fn in SPECS:
            fn = overrides[name] if overrides and name in overrides else side_fn
            symbol_trades, symbol_skips = run_protected_trades(
                records,
                symbol=symbol,
                strategy=name,
                side_at=fn,
                max_hold=hold,
                invalidated=invalid,
                level_at=level_fn,
                study_start=STUDY_START,
                study_end=STUDY_END,
            )
            trades.extend(symbol_trades)
            skips.extend(symbol_skips)
    return trades, skips


def _run_options(frames, split_dates, underlying, store, workers, premium_fn, last_complete):
    symbols = [symbol for symbol in OPTION_SYMBOLS if symbol in frames]

    def work(symbol: str):
        try:
            stock = [trade for trade in underlying if trade["symbol"] == symbol]
            directional, d_skips, d_unmarked = price_directional(
                symbol, frames[symbol], stock, split_dates.get(symbol, []), store.load_chain
            )
            premium, p_skips, p_unmarked = price_premium(
                symbol,
                frames[symbol],
                split_dates.get(symbol, []),
                store.load_chain,
                STUDY_START,
                last_complete,
                side_at=premium_fn,
            )
            print(
                f"options {symbol}: closed {len(directional) + len(premium)}, unmarked {len(d_unmarked) + len(p_unmarked)}",
                flush=True,
            )
            return directional + premium, d_skips + p_skips, d_unmarked + p_unmarked
        except Exception as exc:
            store.note("options", f"{type(exc).__name__}: {exc}", symbol)
            print(f"options {symbol} failed: {exc}", flush=True)
            return [], [], []

    trades: list[dict] = []
    skips: list[dict] = []
    unmarked: list[dict] = []
    if not symbols:
        return trades, skips, unmarked
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(work, symbol) for symbol in symbols]
        for fut in as_completed(futures):
            symbol_trades, symbol_skips, symbol_unmarked = fut.result()
            trades.extend(symbol_trades)
            skips.extend(symbol_skips)
            unmarked.extend(symbol_unmarked)
    return trades, skips, unmarked


def _vrp_rows(frames, indexes, last_complete) -> list[dict]:
    rows: list[dict] = []
    for symbol in OPTION_SYMBOLS:
        records = frames.get(symbol)
        if not records:
            continue
        rows.extend(
            variance_risk_observations(
                records,
                symbol=symbol,
                source="vendor_iv",
                study_start=STUDY_START,
                study_end=last_complete,
                side_at=premium_side,
                horizon=PREMIUM_HOLD,
            )
        )
    proxies = (("QQQ", "VXN"), ("IWM", "RVX"))
    for symbol, index_name in proxies:
        records = frames.get(symbol)
        series = indexes.get(index_name) or []
        if not records or not series:
            continue
        points = [(row["date"], float(row["close"]) / 100.0) for row in series if row["date"] <= last_complete]
        overlay = with_external_iv(records, points)
        rows.extend(
            variance_risk_observations(
                overlay,
                symbol=symbol,
                source="index_iv_proxy",
                study_start=STUDY_START,
                study_end=last_complete,
                side_at=premium_side,
                horizon=PREMIUM_HOLD,
            )
        )
    return rows


def _apply_sentiment(probe, frames, split_dates, store, workers, last_complete) -> dict:
    chosen = _choose_sentiment(probe, _spy_days(frames, last_complete))
    if chosen is None or not frames:
        return {"applied": False, "trades": []}
    scores = {day: value for day, value in chosen["points"]}
    medians = _exclusive_stat(chosen["points"], IV_PCT_WINDOW, statistics.median)
    deciles = _exclusive_stat(chosen["points"], IV_PCT_WINDOW, lambda values: _quantile(values, 0.10))
    overrides = {}
    for name, side_fn, _hold, _invalid, _level in SPECS:
        overrides[name] = mask_side(side_fn, chosen["kind"], name, scores, medians, deciles)
    premium_fn = mask_side(premium_side, chosen["kind"], PREMIUM, scores, medians, deciles)
    underlying, _skips = _run_underlying(frames, overrides)
    options, _option_skips, _unmarked = _run_options(
        frames, split_dates, underlying, store, workers, premium_fn, last_complete
    )
    tagged = _retag(underlying, "underlying_proxy_sentiment_filter") + _retag(options, "direct_option_sentiment_filter")
    return {
        "applied": True,
        "kind": chosen["kind"],
        "label": chosen["label"],
        "coverage": chosen["coverage"],
        "trades": tagged,
    }


def _choose_sentiment(probe: dict, study_days: list[date]) -> dict | None:
    if not study_days:
        return None
    candidates = []
    if probe.get("gdelt"):
        candidates.append(("news_tone", 'GDELT DOC timelinetone for "S&P 500"', probe["gdelt"]))
    if probe.get("cnn"):
        candidates.append(("fear_greed", "CNN Fear and Greed historical score", probe["cnn"]))
    put_call = probe.get("equity_put_call") or []
    if put_call and put_call[-1]["date"] >= STUDY_START:
        candidates.append(("put_call", "CBOE equity put/call ratio", [(row["date"], row["put_call"]) for row in put_call]))
    for kind, label, points in candidates:
        daily = _daily_mean(points)
        have = {day for day, _value in daily}
        coverage = sum(1 for day in study_days if day in have) / len(study_days)
        if coverage >= 0.80:
            return {"kind": kind, "label": label, "points": daily, "coverage": coverage}
    return None


def _spy_days(frames, last_complete) -> list[date]:
    records = frames.get("SPY") or next(iter(frames.values()), [])
    return [row["date"] for row in records if STUDY_START <= row["date"] <= last_complete]


def _daily_mean(points: list[tuple[date, float]]) -> list[tuple[date, float]]:
    buckets: dict[date, list[float]] = defaultdict(list)
    for day, value in points:
        buckets[day].append(float(value))
    return [(day, sum(values) / len(values)) for day, values in sorted(buckets.items())]


def _exclusive_stat(points, window: int, reducer) -> dict[date, float]:
    ordered = sorted(points, key=lambda item: item[0])
    out: dict[date, float] = {}
    values = [value for _day, value in ordered]
    for index in range(window, len(ordered)):
        out[ordered[index][0]] = float(reducer(values[index - window : index]))
    return out


def _quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    index = int(round(q * (len(ordered) - 1)))
    return ordered[index]


def _retag(trades: list[dict], result_type: str) -> list[dict]:
    tagged = []
    for trade in trades:
        row = dict(trade)
        row["result_type"] = result_type
        tagged.append(row)
    return tagged


def _summaries(trades: list[dict]) -> list[dict]:
    keys = {(trade["result_type"], trade["strategy"]) for trade in trades}
    rows = []
    for result_type, strategy in sorted(keys, key=lambda item: (item[0], _ORDER.get(item[1], 9), item[1])):
        subset = [trade for trade in trades if trade["result_type"] == result_type and trade["strategy"] == strategy]
        rows.append({"result_type": result_type, "strategy": strategy, **summarize(subset)})
    return rows


def _compare_unmarked(option_trades: list[dict], unmarked: list[dict]) -> list[dict]:
    strategies = sorted({row["strategy"] for row in option_trades + unmarked}, key=lambda name: _ORDER.get(name, 9))
    compared = []
    for strategy in strategies:
        marked = [row.get("underlying_return") for row in option_trades if row["strategy"] == strategy and row.get("status") == "closed"]
        missing = [row.get("underlying_return") for row in unmarked if row["strategy"] == strategy]
        compared.append(
            {
                "strategy": strategy,
                "marked_n": sum(1 for value in marked if value is not None),
                "marked_mean_underlying": _mean([value for value in marked if value is not None]),
                "unmarked_n": sum(1 for value in missing if value is not None),
                "unmarked_mean_underlying": _mean([value for value in missing if value is not None]),
            }
        )
    return compared


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _count(skips: list[dict]) -> dict:
    counts: dict[str, int] = defaultdict(int)
    for skip in skips:
        counts[f"{skip.get('strategy')}|{skip.get('reason')}"] += 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _backdrop(frames, indexes, diagnostics, last_complete, session_rule, prices) -> dict:
    spy_records = frames.get("SPY") or []
    study = [row for row in spy_records if STUDY_START <= row["date"] <= last_complete]
    spy = {}
    if study:
        counts: dict[str, int] = defaultdict(int)
        for row in study:
            counts[row["trend_regime"]] += 1
        spy = {
            "start_date": study[0]["date"].isoformat(),
            "end_date": study[-1]["date"].isoformat(),
            "start_close": study[0]["close"],
            "end_close": study[-1]["close"],
            "return": study[-1]["close"] / study[0]["close"] - 1,
            "sessions": len(study),
            "trend_counts": dict(counts),
        }
    vix_rows = [row for row in (indexes.get("VIX") or []) if STUDY_START <= row["date"] <= last_complete]
    vix = {}
    if vix_rows:
        high = max(vix_rows, key=lambda row: row["high"])
        low = min(vix_rows, key=lambda row: row["low"])
        vix = {
            "start": vix_rows[0]["close"],
            "end": vix_rows[-1]["close"],
            "max": high["high"],
            "max_date": high["date"].isoformat(),
            "min": low["low"],
            "min_date": low["date"].isoformat(),
        }
    pairs = []
    vix_map = {row["date"]: row["close"] / 100.0 for row in indexes.get("VIX") or []}
    for row in study:
        iv = row.get("iv")
        implied = vix_map.get(row["date"])
        if iv is None or implied is None:
            continue
        pairs.append((float(iv), implied))
    corr = pearson([item[0] for item in pairs], [item[1] for item in pairs]) if pairs else None
    mean_diff = _mean([item[0] - item[1] for item in pairs]) if pairs else None
    split_rows = []
    for item in diagnostics:
        split_rows.extend(item["splits"])
    priced = [item["symbol"] for item in diagnostics]
    return {
        "warmup_start": WARMUP_START.isoformat(),
        "first_session": STUDY_START.isoformat(),
        "requested_end": STUDY_END.isoformat(),
        "last_complete": last_complete.isoformat(),
        "session_rule": session_rule,
        "spy": spy,
        "vix": vix,
        "iv_vix_n": len(pairs),
        "iv_vix_corr": corr,
        "iv_vix_mean_diff": mean_diff,
        "priced_symbols": priced,
        "missing_price_symbols": [symbol for symbol in PRICE_SYMBOLS if symbol not in frames],
        "option_symbols": [symbol for symbol in OPTION_SYMBOLS if symbol in frames],
        "splits": split_rows,
        "reference_equity": EQUITY0,
        "dropped_price_dates": sorted(
            {
                bar["date"].isoformat()
                for bars in prices.values()
                for bar in bars
                if bar["date"] > last_complete
            }
        ),
    }


def _write_cached_tables(root: Path, frames, vols, indexes, splits) -> None:
    price_path = root / "prices.csv"
    with price_path.open("w", newline="") as handle:
        fields = ["symbol", "date", "open", "high", "low", "close", "volume", "raw_close"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for symbol, records in sorted(frames.items()):
            for row in records:
                writer.writerow({field: _cell(row.get(field) if field != "symbol" else symbol) for field in fields})
    vol_path = root / "volatility_history.csv"
    with vol_path.open("w", newline="") as handle:
        fields = ["symbol", "date", "iv_current", "hv_current", "iv_year_high", "iv_year_low"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for symbol, rows in sorted(vols.items()):
            for row in rows:
                writer.writerow({field: _cell(row.get(field)) for field in fields})
    index_path = root / "index_vol.csv"
    with index_path.open("w", newline="") as handle:
        fields = ["symbol", "date", "open", "high", "low", "close"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for name, rows in sorted(indexes.items()):
            for row in rows:
                writer.writerow(
                    {
                        "symbol": name,
                        "date": _cell(row["date"]),
                        "open": _cell(row["open"]),
                        "high": _cell(row["high"]),
                        "low": _cell(row["low"]),
                        "close": _cell(row["close"]),
                    }
                )
    split_path = root / "splits.csv"
    with split_path.open("w", newline="") as handle:
        fields = ["symbol", "ex_date", "numerator", "denominator"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for symbol, items in sorted(splits.items()):
            for split in items:
                writer.writerow(
                    {
                        "symbol": symbol,
                        "ex_date": split.ex_date.isoformat(),
                        "numerator": split.numerator,
                        "denominator": split.denominator,
                    }
                )


def _write_outputs(output: Path, result: dict) -> None:
    trade_fields = [
        "result_type", "strategy", "symbol", "side", "status", "signal_date", "entry_date", "exit_date",
        "exit_reason", "structure", "expiration", "long_strike", "short_strike", "premium", "width",
        "contracts", "shares", "entry_price", "exit_price", "stop_price", "max_loss", "risk_dollars",
        "commissions", "pnl", "unrealized_pnl", "r_multiple", "trend_regime", "vol_regime",
        "entry_iv", "entry_rv20", "iv_percentile", "short_iv", "spot", "underlying_return",
    ]
    with (output / "trades.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=trade_fields, extrasaction="ignore")
        writer.writeheader()
        for trade in result["trades"]:
            writer.writerow({field: _cell(trade.get(field)) for field in trade_fields})
    vrp_fields = [
        "result_type", "symbol", "signal_date", "end_date", "side", "iv", "forward_rv", "iv_minus_rv",
        "variance_gap", "underlying_return", "expected_move", "inside_expected_move",
        "adverse_beyond_expected_move", "trend_regime", "vol_regime", "horizon_sessions",
    ]
    with (output / "vrp.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=vrp_fields)
        writer.writeheader()
        for row in result["vrp_rows"]:
            writer.writerow({field: _cell(row.get(field)) for field in vrp_fields})
    scan_fields = [
        "symbol", "strategy", "side", "as_of", "supported", "historical_n", "historical_mean_r",
        "historical_expectancy", "evidence", "why", "invalidation", "max_loss", "pass_if", "illustration_note",
    ]
    with (output / "scan.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=scan_fields, extrasaction="ignore")
        writer.writeheader()
        for row in result["scan"]:
            writer.writerow({field: _cell(row.get(field)) for field in scan_fields})
    payload = {key: value for key, value in result.items() if key not in ("trades", "vrp_rows")}
    (output / "stats.json").write_text(json.dumps(payload, indent=2, default=_json_default))
    (output / "scan.json").write_text(json.dumps(result["scan"], indent=2, default=_json_default))
    (output / "run_manifest.json").write_text(
        json.dumps(
            {
                "backdrop": result["backdrop"],
                "chain_counts": result["chain_counts"],
                "errors": result["errors"],
                "skip_counts": result["skip_counts"],
                "diagnostics": result["diagnostics"],
                "sentiment_attempts": result["sentiment"]["attempts"],
                "sentiment_applied": result["sentiment"]["applied"],
            },
            indent=2,
            default=_json_default,
        )
    )


def _cell(value):
    if value is None:
        return ""
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, float):
        return f"{value:.8f}".rstrip("0").rstrip(".")
    if isinstance(value, bool):
        return "true" if value else "false"
    return value


def _json_default(value):
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    raise TypeError(f"not serializable: {type(value)}")


if __name__ == "__main__":
    sys.exit(main())
