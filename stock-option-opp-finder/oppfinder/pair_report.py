"""Report for a named pair. Numbers come only from that run."""

from __future__ import annotations

from oppfinder.config import MIN_SAMPLE
from oppfinder.report import headline_sentence

_FRONTMATTER = """---
cursor:
  subagentId: "bc-172f6af4-0e27-5f88-8a92-585c40517130"
---

"""


def render_pair(result: dict, *, frontmatter: bool = False) -> str:
    names = ", ".join(result["backdrop"].get("priced_symbols") or [])
    body = "\n".join(
        [
            f"# SPY and NBIS, {result['backdrop']['first_session']} through {result['backdrop']['last_complete']}",
            "",
            _lead(result),
            "",
            "## The two paths",
            "",
            _paths(result),
            "",
            "## Managed trades",
            "",
            _managed(result),
            "",
            "## Drift after the same signals",
            "",
            _events(result),
            "",
            "## Listed SPY verticals and the NBIS option gap",
            "",
            _options(result),
            "",
            "## What is on the board now",
            "",
            _scan(result),
            "",
            "## Sentiment",
            "",
            _sentiment(result),
            "",
            "## How to read this",
            "",
            _limits(result),
            "",
            "This is research, not a recommendation to trade. "
            f"The names in this run: {names}.",
            "",
        ]
    )
    if frontmatter:
        return _FRONTMATTER + body
    return body


def _lead(result: dict) -> str:
    option = headline_sentence(result["headline_option"]["status"], result["headline_option"].get("row"), "listed-option")
    proxy = headline_sentence(result["headline_proxy"]["status"], result["headline_proxy"].get("row"), "stock-proxy")
    events = [
        row
        for row in result.get("event_summaries") or []
        if row.get("overlap") == "non_overlapping" and row.get("evidence") == "positive_interval_above_zero"
    ]
    if events:
        best = max(events, key=lambda row: row.get("ci95_low") or -1e9)
        event_line = (
            f"The non-overlapping close-to-close drift with a positive interval is "
            f"{best['symbol']} {best['strategy']} over {best['horizon']} sessions "
            f"(n={best['n']}, mean signed return {_p(best.get('mean_signed_return'))})."
        )
    else:
        event_line = (
            f"No non-overlapping signal window reached {MIN_SAMPLE} observations with a positive interval "
            "for the signed close-to-close return. Those windows are a drift check, not a filled trade."
        )
    held = result.get("paths") or []
    path_bits = [
        f"{row['symbol']} {_p(row.get('simple_return'))} from {row.get('start_close') and _n(row.get('start_close'), 2)} "
        f"to {_n(row.get('end_close'), 2)}"
        for row in held
        if row.get("simple_return") is not None
    ]
    path_line = "Buy-and-hold over this one window: " + "; ".join(path_bits) + ". One path is not a strategy sample."
    return " ".join([path_line, proxy, option, event_line])


def _paths(result: dict) -> str:
    lines = [
        f"Session rule: {result['backdrop'].get('session_rule')}",
        "",
    ]
    rows = [["Symbol", "Sessions", "Return", "Max DD", "Realized vol", "Avg shares", "Avg dollars"]]
    for row in result.get("paths") or []:
        rows.append(
            [
                row["symbol"],
                str(row.get("sessions")),
                _p(row.get("simple_return")),
                _p(row.get("max_drawdown")),
                _p(row.get("realized_vol")),
                _shares(row.get("avg_share_volume")),
                _dollars(row.get("avg_dollar_volume")),
            ]
        )
    lines.append(_table(rows))
    for row in result.get("paths") or []:
        lines.append("")
        lines.append(
            f"{row['symbol']} trend labels: {_count_phrase(row.get('trend_counts') or {})}. "
            f"Vol labels: {_count_phrase(row.get('vol_counts') or {})}."
        )
    link = result.get("link") or {}
    if link.get("n"):
        lines.append("")
        lines.append(
            f"On {link['n']} shared sessions, NBIS daily simple returns versus SPY: "
            f"correlation {_n(link.get('correlation'), 3)}, beta {_n(link.get('beta'), 2)}. "
            "Beta is the covariance divided by SPY's variance. It is a description of this window."
        )
    return "\n".join(lines)


def _managed(result: dict) -> str:
    lines = [
        "Same rules as the full book: next-session open, a 2 ATR stop, 5 bps of adverse slippage, "
        "and 1% of a $100,000 reference per trade. One position per symbol per strategy. "
        f"Below {MIN_SAMPLE} closed trades the average is descriptive only.",
        "",
    ]
    rows = [["Symbol", "Strategy", "Trades", "Win rate", "Expectancy", "Mean R", "Profit factor", "Max DD", "Evidence"]]
    managed = [
        row
        for row in result.get("by_symbol") or []
        if row.get("result_type") == "underlying_proxy" and row.get("n")
    ]
    if not managed:
        lines.append("No closed stock-proxy trades.")
        return "\n".join(lines)
    for row in managed:
        rows.append(
            [
                row["symbol"],
                row["strategy"],
                str(row["n"]),
                _p(row.get("win_rate")),
                _m(row.get("expectancy")),
                _n(row.get("mean_r"), 3),
                _pf(row.get("profit_factor")),
                _p(row.get("max_drawdown")),
                row["evidence"],
            ]
        )
    lines.append(_table(rows))
    return "\n".join(lines)


def _events(result: dict) -> str:
    lines = [
        "Each row is the signed percent change from the signal close to the close a fixed number of sessions later. "
        "A short signal that falls is a positive signed return. There is no stop, no slippage, and no commission. "
        "Rows marked overlapping share days, so that label is not a significance test. "
        "The evidence words apply only to the non-overlapping rows.",
        "",
    ]
    rows = [["Symbol", "Signal", "Hold", "Overlap", "N", "Mean signed", "Win rate", "Evidence"]]
    body = result.get("event_summaries") or []
    if not body:
        return "No signal had a complete forward window."
    for row in body:
        if row["n"] == 0:
            continue
        rows.append(
            [
                row["symbol"],
                row["strategy"],
                str(row["horizon"]),
                row["overlap"].replace("_", " "),
                str(row["n"]),
                _p(row.get("mean_signed_return")),
                _p(row.get("win_rate")),
                row["evidence"],
            ]
        )
    if len(rows) == 1:
        return "No signal had a complete forward window."
    lines.append(_table(rows))
    return "\n".join(lines)


def _options(result: dict) -> str:
    lines = []
    for note in result.get("coverage_notes") or []:
        lines.append(note)
    if lines:
        lines.append("")
    direct = [row for row in result.get("by_symbol") or [] if row.get("result_type") == "direct_option" and row.get("n")]
    if not direct:
        lines.append("No listed vertical closed in this run.")
    else:
        lines.append(
            "SPY verticals use the end-of-day bid and ask on the sampled strike grid. "
            "A missing exit quote stays missing."
        )
        lines.append("")
        rows = [["Symbol", "Strategy", "Trades", "Win rate", "Expectancy", "Mean R", "Profit factor", "Evidence"]]
        for row in direct:
            rows.append(
                [
                    row["symbol"],
                    row["strategy"],
                    str(row["n"]),
                    _p(row.get("win_rate")),
                    _m(row.get("expectancy")),
                    _n(row.get("mean_r"), 3),
                    _pf(row.get("profit_factor")),
                    row["evidence"],
                ]
            )
        lines.append(_table(rows))
    unmarked = result.get("unmarked_compare") or []
    if unmarked:
        lines.append("")
        lines.append("Unmarked exits, compared on the underlying return over the intended hold:")
        for row in unmarked:
            lines.append(
                f"- {row['strategy']}: unmarked n={row['unmarked_n']}, mean underlying {_p(row.get('unmarked_mean_underlying'))}; "
                f"marked n={row['marked_n']}, mean underlying {_p(row.get('marked_mean_underlying'))}."
            )
    vrp = result.get("vrp_summaries") or []
    if vrp:
        lines.append("")
        for block in vrp:
            summary = block["summary"]
            if not summary.get("n"):
                continue
            lines.append(
                f"{block['label']}: {summary.get('note')} "
                f"Mean IV minus forward realized vol {_n(summary.get('mean_iv_minus_rv'), 4)}. "
                f"Mean of IV squared minus realized vol squared {_n(summary.get('mean_variance_gap'), 4)}. "
                f"Fraction with realized vol below IV {_p(summary.get('fraction_rv_below_iv'))}."
            )
    return "\n".join(lines)


def _scan(result: dict) -> str:
    scan = result.get("scan") or []
    if not scan:
        return "Neither name matched a rule on the last completed session."
    lines = [
        "A match means the last completed bar passed a rule. It is not a trade instruction. "
        "The history next to it is this two-name run, and a sample under 30 is not a reason to take the trade.",
        "",
    ]
    for row in scan:
        lines.append(
            f"- **{row['symbol']} {row['strategy']} {row['side']}** as of {row['as_of']}. "
            f"Why: {row['why']}. Invalidation: {row['invalidation']} "
            f"Risk: {row['max_loss']} Pass if: {row['pass_if']} "
            f"Pooled history in this run: n={row['historical_n']}, mean R {_n(row.get('historical_mean_r'), 3)}, "
            f"{row['evidence']}."
        )
    return "\n".join(lines)


def _sentiment(result: dict) -> str:
    sent = result.get("sentiment") or {}
    lines = ["A sentiment score is used only when a free source covers the window. Failed calls stay blank."]
    for attempt in sent.get("attempts") or []:
        lines.append(f"- {attempt.get('source')}: {attempt.get('result')}")
    if sent.get("applied"):
        lines.append(f"A filter was applied ({sent.get('label')}). The tables above stay unfiltered.")
    else:
        lines.append("No sentiment filter was applied.")
    return "\n".join(lines)


def _limits(result: dict) -> str:
    chain = result.get("chain_counts") or {}
    return "\n".join(
        [
            "Downloaded history starts at the first Yahoo bar: "
            + "; ".join(
                f"{item['symbol']} {item['first']}" for item in (result.get("diagnostics") or [])
            )
            + ". Indicators that need more bars than that history stay blank until they exist.",
            "",
            "The four rules were fixed before this pair was run. Nothing in this report was chosen by searching thresholds. "
            "Two names in one year do not produce a large independent sample, and NBIS moves with the same market as SPY.",
            "",
            f"Chain lookups: ok {chain.get('ok', 0)}, empty {chain.get('empty', 0)}, errors {chain.get('error', 0)}.",
            "",
            "Top skip reasons: " + _skips(result.get("skip_counts") or {}),
        ]
    )


def _count_phrase(counts: dict) -> str:
    total = sum(counts.values()) or 1
    parts = [f"{name} {count} ({count / total:.0%})" for name, count in counts.items() if count]
    return ", ".join(parts) if parts else "none"


def _skips(counts: dict) -> str:
    if not counts:
        return "none."
    return "; ".join(f"{key} {value}" for key, value in list(counts.items())[:8]) + "."


def _table(rows: list[list[str]]) -> str:
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


def _shares(value) -> str:
    if value is None:
        return "n/a"
    return f"{value:,.0f}"


def _dollars(value) -> str:
    if value is None:
        return "n/a"
    return f"${value:,.0f}"
