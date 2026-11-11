"""Turn a completed run into the markdown report. Numbers come only from that run."""

from __future__ import annotations

from typing import Literal

from oppfinder.config import (
    ATR_STOP_MULT,
    EQUITY0,
    IV_PERCENTILE_MIN,
    MAX_ONE_LOT_RISK_FRAC,
    MIN_SAMPLE,
    OPTION_COMMISSION,
    PREMIUM_HOLD,
    RISK_FRAC,
    STOCK_SLIPPAGE_BPS,
)
from oppfinder.stats import EvidenceLabel

HeadlineStatus = Literal[
    "supported",
    "positive_not_significant",
    "all_samples_too_small",
    "no_positive_edge",
    "no_trades",
]

_FRONTMATTER = """---
cursor:
  subagentId: "bc-172f6af4-0e27-5f88-8a92-585c40517130"
---

"""


def render_findings(result: dict, *, frontmatter: bool = False) -> str:
    body = "\n".join(
        [
            f"# What the last year paid, {result['backdrop']['first_session']} through {result['backdrop']['last_complete']}",
            "",
            _lead(result),
            "",
            "## The market behind the window",
            "",
            _backdrop(result["backdrop"]),
            "",
            "## How a trade was counted",
            "",
            _method(),
            "",
            "## Listed option verticals",
            "",
            _book(
                result,
                "direct_option",
                "These are end-of-day bid/ask fills on one-strike verticals from the DoltHub chain. "
                "A missing exit quote is left unmarked. It is not replaced with a model price.",
            ),
            "",
            "## Stock proxies for the same signals",
            "",
            _book(
                result,
                "underlying_proxy",
                "Same entry rules, but the fill is the stock: next-session open, a 2 ATR stop, "
                f"and {STOCK_SLIPPAGE_BPS:.0f} bps of adverse slippage. This is not an option payoff. "
                "Premium selling has no stock-stop version, because a stop on the shares does not match a credit spread.",
            ),
            "",
            "## Regimes",
            "",
            _regimes(result),
            "",
            "## Implied vol versus the vol that followed",
            "",
            _vrp(result),
            "",
            "## Unmarked option exits",
            "",
            _unmarked(result),
            "",
            "## Current scan",
            "",
            _scan(result),
            "",
            "## Sentiment",
            "",
            _sentiment(result),
            "",
            "## What can make this misleading",
            "",
            _limits(result),
            "",
            "## Reproduce",
            "",
            "From `stock-option-opp-finder`:",
            "",
            "```",
            "python3 -m oppfinder",
            "python3 -m pytest",
            "```",
            "",
            "The run writes `output/trades.csv`, `output/stats.json`, `output/scan.json`, `output/vrp.csv`, and `output/summary.md`. Cached downloads live in `data/`. This is research, not a recommendation to trade.",
            "",
        ]
    )
    if frontmatter:
        return _FRONTMATTER + body
    return body


def headline_sentence(status: HeadlineStatus, row: dict | None, kind_label: str) -> str:
    if status == "supported" and row is not None:
        return (
            f"The clearest supported {kind_label} result is {row['strategy']}. "
            f"It closed {row['n']} trades with mean R {_n(row.get('mean_r'), 3)}, "
            f"win rate {_p(row.get('win_rate'))}, expectancy {_m(row.get('expectancy'))} per trade, "
            f"and profit factor {_pf(row.get('profit_factor'))}. "
            f"The normal 95% interval for mean R is [{_n(row.get('ci95_low'), 3)}, {_n(row.get('ci95_high'), 3)}]. "
            f"{row.get('note', '')}"
        )
    if status == "positive_not_significant" and row is not None:
        return (
            f"No {kind_label} strategy has a mean R whose normal 95% interval sits above zero. "
            f"The highest positive average with at least {MIN_SAMPLE} closed trades is {row['strategy']}: "
            f"mean R {_n(row.get('mean_r'), 3)}, n={row['n']}, interval "
            f"[{_n(row.get('ci95_low'), 3)}, {_n(row.get('ci95_high'), 3)}]. "
            "That interval includes zero, so this is a point estimate rather than a demonstrated edge."
        )
    if status == "all_samples_too_small":
        return (
            f"No {kind_label} strategy reached {MIN_SAMPLE} closed trades. "
            "Averages in that book are descriptive only. None is treated as a winner."
        )
    if status == "no_positive_edge" and row is not None:
        return (
            f"No {kind_label} strategy with at least {MIN_SAMPLE} closed trades has a positive average R. "
            f"The highest average is {row['strategy']} at {_n(row.get('mean_r'), 3)} (n={row['n']})."
        )
    if status == "no_trades":
        return f"The run produced no closed {kind_label} trades."
    if status == "supported":
        return f"The {kind_label} headline was marked supported without a row. That is an internal error."
    if status == "positive_not_significant":
        return f"A positive {kind_label} estimate was flagged without a row. That is an internal error."
    if status == "no_positive_edge":
        return f"The {kind_label} book had no usable row. That is an internal error."
    _never_status(status)
    return ""


def _never_status(status: HeadlineStatus) -> None:
    raise AssertionError(status)


def _lead(result: dict) -> str:
    option = headline_sentence(
        result["headline_option"]["status"],
        result["headline_option"].get("row"),
        "listed-option",
    )
    proxy = headline_sentence(
        result["headline_proxy"]["status"],
        result["headline_proxy"].get("row"),
        "stock-proxy",
    )
    scan = result.get("scan") or []
    supported = [row for row in scan if row.get("supported")]
    if supported:
        names = ", ".join(f"{row['symbol']} {row['strategy']} {row['side']}" for row in supported)
        scan_line = f"On the last completed session, the scan finds these supported matches: {names}."
    else:
        scan_line = (
            "On the last completed session, no name matches a setup whose historical sample "
            f"cleared {MIN_SAMPLE} trades and a positive interval for mean R."
        )
    return " ".join([option, proxy, scan_line])


def _backdrop(backdrop: dict) -> str:
    spy = backdrop.get("spy") or {}
    vix = backdrop.get("vix") or {}
    lines = [
        (
            f"Prices run from {backdrop['warmup_start']} so the 200-day average and the 252-day "
            f"volatility percentile exist by {backdrop['first_session']}. "
            f"The tested signals stop at {backdrop['last_complete']}. "
            f"Requested end was {backdrop['requested_end']}. "
            f"Session rule: {backdrop['session_rule']}"
        ),
        "",
        (
            f"SPY adjusted close went from {_n(spy.get('start_close'), 2)} on {spy.get('start_date', 'n/a')} "
            f"to {_n(spy.get('end_close'), 2)} on {spy.get('end_date', 'n/a')}, "
            f"a simple return of {_p(spy.get('return'))}. "
            f"Of {spy.get('sessions', 0)} SPY sessions in the test window, "
            f"{_regime_phrase(spy.get('trend_counts') or {})}."
        ),
        "",
        (
            f"CBOE VIX in the window opened the first session at {_n(vix.get('start'), 2)} and closed the last at "
            f"{_n(vix.get('end'), 2)}. The high was {_n(vix.get('max'), 2)} on {vix.get('max_date', 'n/a')} "
            f"and the low was {_n(vix.get('min'), 2)} on {vix.get('min_date', 'n/a')}."
        ),
        "",
        (
            f"SPY vendor `iv_current` versus VIX/100 on {backdrop.get('iv_vix_n', 0)} overlapping sessions: "
            f"correlation {_n(backdrop.get('iv_vix_corr'), 3)}, mean of (vendor IV minus VIX/100) "
            f"{_n(backdrop.get('iv_vix_mean_diff'), 4)}. "
            "They are related series, not the same number. Signals use the vendor IV, not a rescaled VIX."
        ),
    ]
    priced = ", ".join(backdrop.get("priced_symbols") or [])
    missing = ", ".join(backdrop.get("missing_price_symbols") or []) or "none"
    lines.extend(["", f"Price history loaded for {priced}. Missing price history: {missing}."])
    lines.append(
        "QQQ and IWM are in the stock book. The free option dataset returned no chain and no IV row for them, "
        "so they have no listed-vertical trades. VXN and RVX are used only as an index-IV proxy in the variance study."
    )
    extras = backdrop.get("splits") or []
    if extras:
        rendered = "; ".join(f"{item['symbol']} {item['ex_date']} {item['numerator']:g}-for-{item['denominator']:g}" for item in extras)
        lines.append(f"Yahoo reported splits: {rendered}. Option trades that straddle a split are dropped.")
    else:
        lines.append("Yahoo reported no splits in the downloaded history.")
    return "\n".join(lines)


def _regime_phrase(counts: dict) -> str:
    if not counts:
        return "regime counts were unavailable"
    total = sum(counts.values()) or 1
    parts = [f"{name} {count} ({count / total:.0%})" for name, count in counts.items() if count]
    return ", ".join(parts)


def _method() -> str:
    return "\n".join(
        [
            "Signals use only the close they are stamped with. Stock proxies buy or sell the next session's open. "
            f"Stops are {ATR_STOP_MULT:.0f} times the 14-day ATR. A stop touched intraday fills at the stop; "
            "a gap through the stop fills at the open. Both then take "
            f"{STOCK_SLIPPAGE_BPS:.0f} bps of adverse slippage. Stock commission is zero. "
            f"Each trade risks {RISK_FRAC:.0%} of a ${EQUITY0:,.0f} reference (${EQUITY0 * RISK_FRAC:,.0f}). "
            "Size does not compound. One position per symbol per strategy.",
            "",
            "Listed verticals are one strike wide on the DoltHub end-of-day grid. "
            "Debit spreads buy the leg nearest a 0.45 delta and sell the next further strike. "
            "Credit spreads sell the leg nearest a 0.30 delta and buy the next further strike. "
            "Natural prices: buy at the ask, sell at the bid. "
            f"Commission is ${OPTION_COMMISSION} per contract per leg per side. "
            f"One contract is allowed up to {MAX_ONE_LOT_RISK_FRAC:.1%} of the reference account; wider risk is skipped. "
            "The option entry is the end-of-day chain on the session after the signal, because that dataset has no open quotes. "
            "The option exit is the end-of-day chain on the session the stock rule exits, or up to two later sessions if those exact strikes are missing. "
            "Same-session option round trips are dropped. There is one quote per day, so it cannot be both the entry and the exit.",
            "",
            "Trend continuation is a cross back through the 20-day average while the 50-day average is sloping with the trade and price is on that side of the 50-day. Hold is 15 sessions or until price closes back through the 50-day. "
            "Mean reversion buys a stretch in an uptrend: close above the 200-day, RSI(2) under 10, and close under the lower 20-day Bollinger band (2 standard deviations). The short is the mirror under the 200-day. Hold is 5 sessions or a cross back through the 20-day. "
            "Momentum breakout is a close through the prior 20-session high or low, with the 50-day on that side and volume above 1.2 times the prior 20-session average. Hold is 10 sessions or a close back through the broken level. "
            f"High-IV premium selling requires an IV percentile of at least {IV_PERCENTILE_MIN:.2f} inside the trailing {252} vendor readings and vendor IV above 20-day realized vol. Above the 50-day it sells a put vertical; below the 50-day it sells a call vertical. Hold is {PREMIUM_HOLD} sessions or an underlying close through the short strike.",
            "",
            "Trend regime: uptrend when close and the 50-day are both above the 200-day; downtrend when both are below; otherwise range. "
            "Vol regime: high when 20-day realized vol is at or above the median of the prior 252 readings. "
            "Expectancy is the mean P&L, scratches included. Profit factor is gross wins over absolute gross losses, and it is undefined when there is no loss. "
            "R is P&L divided by the defined risk (stop risk for stock, theoretical vertical max loss for options). "
            f"A normal 95% interval is reported only as a rough check. Below {MIN_SAMPLE} closed trades the average is descriptive only.",
        ]
    )


def _book(result: dict, result_type: str, intro: str) -> str:
    rows = [row for row in result["summaries"] if row["result_type"] == result_type]
    if not rows:
        return intro + "\n\nNo closed trades."
    headers = ["Strategy", "Trades", "Win rate", "Avg win", "Avg loss", "Expectancy", "Mean R", "Profit factor", "Max DD", "Evidence"]
    table = [headers]
    for row in rows:
        table.append(
            [
                row["strategy"],
                str(row["n"]),
                _p(row["win_rate"]),
                _m(row["avg_win"]),
                _m(row["avg_loss"]),
                _m(row["expectancy"]),
                _n(row["mean_r"], 3),
                _pf(row["profit_factor"]),
                _p(row["max_drawdown"]),
                row["evidence"],
            ]
        )
    notes = "\n".join(f"- **{row['strategy']}** (n={row['n']}): {row['note']}" for row in rows)
    return intro + "\n\n" + _markdown_table(table) + "\n\n" + notes


def _regimes(result: dict) -> str:
    headers = ["Book", "Strategy", "Slice", "Trades", "Mean R", "Expectancy", "Evidence"]
    table = [headers]
    for row in result["summaries"]:
        if row["result_type"] not in ("direct_option", "underlying_proxy"):
            continue
        for field, keys in (("by_trend", ("uptrend", "downtrend")), ("by_vol", ("high_vol", "low_vol"))):
            for key in keys:
                slice_row = row[field][key]
                if slice_row["n"] == 0:
                    continue
                table.append(
                    [
                        row["result_type"],
                        row["strategy"],
                        key,
                        str(slice_row["n"]),
                        _n(slice_row["mean_r"], 3),
                        _m(slice_row["expectancy"]),
                        slice_row["evidence"],
                    ]
                )
    if len(table) == 1:
        return "No closed trades fell in the uptrend, downtrend, high-vol, or low-vol slices."
    return (
        "A trade keeps both labels, so the trend rows and the vol rows are two views of the same trades, not a partition. "
        f"Slices under {MIN_SAMPLE} trades stay descriptive.\n\n" + _markdown_table(table)
    )


def _vrp(result: dict) -> str:
    lines = []
    for block in result.get("vrp_summaries") or []:
        lines.append(
            f"**{block['label']}** — {block['summary']['note']} "
            f"Mean IV {_n(block['summary'].get('mean_iv'), 4)}, "
            f"mean forward realized vol {_n(block['summary'].get('mean_forward_rv'), 4)}, "
            f"mean IV minus realized {_n(block['summary'].get('mean_iv_minus_rv'), 4)} vol points, "
            f"mean of IV squared minus realized vol squared {_n(block['summary'].get('mean_variance_gap'), 4)}, "
            f"fraction with realized below implied {_p(block['summary'].get('fraction_rv_below_iv'))}, "
            f"fraction of underlying moves inside the one-standard-deviation expected move "
            f"{_p(block['summary'].get('fraction_inside_expected_move'))}, "
            f"fraction with an adverse move beyond that band {_p(block['summary'].get('fraction_adverse'))}."
        )
        lines.append("")
    if not lines:
        return "No variance windows were measured."
    return "\n".join(lines).strip()


def _unmarked(result: dict) -> str:
    blocks = result.get("unmarked_compare") or []
    if not blocks:
        return "No option trade was left unmarked, or no option entry was attempted."
    lines = [
        "When the exit chain did not contain the same strikes within two sessions, the trade is excluded from expectancy. "
        "The underlying return over that intended hold is still real, and it shows whether the missing quotes were the large moves."
    ]
    for block in blocks:
        lines.append(
            f"- **{block['strategy']}**: unmarked n={block['unmarked_n']}, "
            f"mean underlying return {_p(block['unmarked_mean_underlying'])}; "
            f"marked closed option trades n={block['marked_n']}, "
            f"mean underlying return {_p(block['marked_mean_underlying'])}."
        )
    return "\n".join(lines)


def _scan(result: dict) -> str:
    rows = result.get("scan") or []
    if not rows:
        return (
            f"Nothing in the universe fired a fresh signal on {result['backdrop']['last_complete']}. "
            "That includes names whose history would not have supported a trade."
        )
    supported = [row for row in rows if row["supported"]]
    others = [row for row in rows if not row["supported"]]
    parts = []
    if supported:
        parts.append("These last-session signals match a book whose mean R interval is above zero.")
        parts.append("")
        parts.extend(_scan_block(supported))
    else:
        parts.append(
            "No last-session signal matches a book with a positive mean-R interval and at least "
            f"{MIN_SAMPLE} closed trades."
        )
    if others:
        parts.extend(["", "Other last-session patterns, with the historical sample beside them:", ""])
        parts.extend(_scan_block(others))
    return "\n".join(parts)


def _scan_block(rows: list[dict]) -> list[str]:
    lines = []
    for row in rows:
        structure = row.get("illustrative_structure")
        if structure:
            shown = (
                f"Illustrated {structure['kind']} {structure['right'].lower()} "
                f"{structure['long_strike']:.2f}/{structure['short_strike']:.2f} "
                f"expiring {structure['expiration']}, premium {structure['premium']:.2f}, "
                f"width {structure['width']:.2f}."
            )
        else:
            shown = "No illustrated vertical."
        lines.append(
            f"- **{row['symbol']} {row['strategy']} {row['side']}** ({row['history_result_type']}, "
            f"n={row['historical_n']}, mean R {_n(row.get('historical_mean_r'), 3)}, {row['evidence']}). "
            f"{row['why']}. Invalidation: {row['invalidation']} Risk: {row['max_loss']} Pass if: {row['pass_if']} "
            f"{shown} {row['illustration_note']}"
        )
    return lines


def _sentiment(result: dict) -> str:
    sent = result.get("sentiment") or {}
    lines = ["News and positioning sources were called. A failed call is left blank. No score was filled in."]
    for attempt in sent.get("attempts") or []:
        lines.append(f"- {attempt.get('source')}: {attempt.get('result')}")
    if sent.get("applied"):
        lines.append(
            f"Applied filter: {sent.get('label')} ({sent.get('kind')}), coverage {_p(sent.get('coverage'))} of SPY sessions. "
            "The primary tables above are unfiltered. The filtered book is a second pass."
        )
        lines.append("")
        lines.append(_book({"summaries": sent.get("filtered_summaries") or []}, "direct_option_sentiment_filter", "Filtered listed verticals."))
        lines.append("")
        lines.append(_book({"summaries": sent.get("filtered_summaries") or []}, "underlying_proxy_sentiment_filter", "Filtered stock proxies."))
    else:
        lines.append("No source covered at least 80% of the SPY sessions in the test window, so no sentiment filter was applied.")
    return "\n".join(lines)


def _limits(result: dict) -> str:
    chain = result.get("chain_counts") or {}
    return "\n".join(
        [
            "The chain is not the full listed book. Each snapshot in this dataset is a sampled strike grid and a handful of expirations. "
            "A strike that exists on entry can be absent after a large move, because the grid is recentered on spot. "
            "Dropping those exits can remove the very trades where a debit spread paid or a credit spread was run over. "
            "The unmarked-versus-marked underlying returns above are the check on that bias. They are not option P&L.",
            "",
            "Stock fills use the next open. Option fills use an end-of-day quote on that same session, or on the exit session. "
            "Those clocks differ by hours. Intraday option stops are not visible. Assignment is not modeled. "
            "Early profit-taking at a fixed fraction of the credit was not tested, because that would require a chain every day.",
            "",
            "Names in this universe move together. A t-statistic that treats trades as independent overstates the evidence, "
            "even when the interval is above zero. Drawdown for options is the closed-trade equity curve, not a daily mark.",
            "",
            f"Chain lookups that resolved: ok {chain.get('ok', 0)}, empty {chain.get('empty', 0)}, "
            f"network errors {chain.get('error', 0)}. Cache hits are included in the ok and empty counts "
            f"({chain.get('cache', 0)} hits). Data-source errors recorded: {len(result.get('errors') or [])}.",
            "",
            "Top skip reasons: " + _skip_phrase(result.get("skip_counts") or {}),
        ]
    )


def _skip_phrase(counts: dict) -> str:
    if not counts:
        return "none."
    items = list(counts.items())[:8]
    return "; ".join(f"{key} {value}" for key, value in items) + "."


def _markdown_table(rows: list[list[str]]) -> str:
    header = "| " + " | ".join(rows[0]) + " |"
    rule = "| " + " | ".join("---" for _ in rows[0]) + " |"
    body = ["| " + " | ".join(row) + " |" for row in rows[1:]]
    return "\n".join([header, rule, *body])


def _n(value, digits: int) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.{digits}f}"


def _p(value) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.1%}"


def _m(value) -> str:
    if value is None:
        return "n/a"
    return f"${float(value):,.2f}"


def _pf(value) -> str:
    if value is None:
        return "undefined"
    return f"{float(value):.2f}"


# EvidenceLabel is re-exported for tests that want the closed set.
_ = EvidenceLabel
