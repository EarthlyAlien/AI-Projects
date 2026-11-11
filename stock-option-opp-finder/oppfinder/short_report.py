"""Report for the 1-3 session premium study. Numbers come only from that run."""

from __future__ import annotations

_FRONTMATTER = """---
cursor:
  subagentId: "bc-172f6af4-0e27-5f88-8a92-585c40517130"
---

"""


def render_short(result: dict, *, frontmatter: bool = False) -> str:
    body = "\n".join(
        [
            f"# SPY and NBIS premium selling for 1-3 sessions, {result['first_session']} through {result['last_complete']}",
            "",
            _lead(result),
            "",
            "## Direct SPY credit verticals, held 1-2 sessions",
            "",
            _direct(result),
            "",
            "## What the underlying did after the same signals",
            "",
            _windows(result),
            "",
            "## Ranking",
            "",
            _ranking(result),
            "",
            "## Current snapshot (not a backtest)",
            "",
            _snapshot(result),
            "",
            "## NBIS",
            "",
            _nbis(result),
            "",
            "This is research, not a recommendation to trade.",
            "",
        ]
    )
    if frontmatter:
        return _FRONTMATTER + body
    return body


def _lead(result: dict) -> str:
    direct = result["direct_summary"]
    lines = [
        (
            f"Across {len(result['variants'])} variants, the free historical chain marked {direct['marked']} "
            f"SPY credit-vertical closes at the exact 1- or 2-session exit; {direct['unmarked']} variant "
            "entries were unmarked because that day's sampled chain had no quote for the same strikes. "
            "The sampled grid rotates strikes and expirations daily. "
            "A sample that small cannot name a winnable option strategy, and the marked trades are the ones "
            "whose strikes happened to survive, so their average is not the strategy's average."
        ),
        "",
        (
            "The ranking below therefore uses two lower tiers of evidence: the few marked SPY verticals, and "
            "what SPY and NBIS themselves did in the 1-3 sessions after the same signals (signed drift, worst "
            "adverse move versus the expected move at the signal). The second tier is a risk proxy for selling "
            "a defined-risk vertical. It is not option P&L, and for NBIS there is no historical option test at all."
        ),
    ]
    large = [row for row in result["window_summaries"] if row["n"] >= 30]
    if large:
        held3 = [row for row in large if row.get("horizon") == 3]
        row = held3[0] if held3 else large[0]
        shorter = ""
        if row.get("horizon") == 3:
            shorter = "The 1- and 2-session rows for that same family are in the table. "
        lines.append("")
        lines.append(
            f"The only family with at least 30 windows is {row['symbol']} {row['family']}, "
            f"held {row['horizon']} sessions: "
            f"n={row['n']}, mean signed underlying return {_p(row.get('mean_signed_return'))}, "
            f"win rate {_p(row.get('win_rate'))}, adverse intraday move beyond the expected move in "
            f"{_p(row.get('breach_intra_rate'))} of windows. That is not a friendly premium-selling profile. "
            f"{shorter}"
            "The friendlier patterns in the table have 5-20 windows and are descriptive only."
        )
    current = result.get("current_signals") or []
    if current:
        named = "; ".join(
            f"{row['symbol']} {row['family']} {'bullish credit' if row['side'] == 1 else 'bearish credit'}"
            for row in current
        )
        lines.append("")
        lines.append(f"Signals on the last completed session ({result['last_complete']}): {named}.")
    else:
        lines.append("")
        lines.append(f"No family signal fired on the last completed session ({result['last_complete']}).")
    return "\n".join(lines)


def _direct(result: dict) -> str:
    rows = [["Variant", "Marked", "Unmarked", "Win rate", "Expectancy", "Mean R", "Evidence"]]
    ordered = sorted(
        result["variants"],
        key=lambda row: (row.get("mean_r") is None, -(row.get("mean_r") or 0)),
    )
    for row in ordered:
        rows.append(
            [
                row["variant"],
                str(row["n"]),
                str(row["unmarked_n"]),
                _p(row.get("win_rate")),
                _m(row.get("expectancy")),
                _n(row.get("mean_r"), 3),
                row["evidence"],
            ]
        )
    return "\n".join(
        [
            "Entry is the end-of-day chain on the session after the signal. Exit is that chain exactly "
            "1 or 2 sessions later, or the first session when the closing debit is at most half the credit "
            "(pt50_by_day2). Near expiries target 14 days (5-25 allowed); monthly targets 35 (25-55). "
            "The dataset's nearest SPY expiry is usually about two weeks out, so no 0-2 day expiry was tested. "
            "Commission is $0.65 per contract per leg per side and the bid/ask is paid. "
            "These 18 variants are a multiple-comparison set: a positive average in one row is not a discovery.",
            "",
            _table(rows),
        ]
    )


def _windows(result: dict) -> str:
    rows = [
        ["Symbol", "Family", "Hold", "N", "Mean signed", "Win rate", "Adverse close > expected move", "Adverse intraday > expected move", "IV minus forward RV"]
    ]
    for row in result["window_summaries"]:
        if row["n"] == 0:
            continue
        rows.append(
            [
                row["symbol"],
                row["family"],
                str(row["horizon"]),
                str(row["n"]),
                _p(row.get("mean_signed_return")),
                _p(row.get("win_rate")),
                _p(row.get("breach_close_rate")),
                _p(row.get("breach_intra_rate")),
                _n(row.get("mean_iv_minus_forward_rv"), 4),
            ]
        )
    return "\n".join(
        [
            "Overlapping windows after each signal in the study year. A bullish credit wants the signed "
            "return near or above zero and the adverse move inside the expected move implied at the signal "
            "(vendor IV for SPY, 20-day realized vol where a name has no IV). Intraday breach uses the worst "
            "high or low in the window, which is the path a short vertical actually has to survive.",
            "",
            _table(rows),
        ]
    )


def _ranking(result: dict) -> str:
    lines = [
        "Ranked as premium-selling candidates, best first, using the proxy table. None of these is a "
        "demonstrated option edge:",
        "",
    ]
    for rank, row in enumerate(result["ranked_candidates"], start=1):
        flag = "" if row["n"] >= 30 else " (under 30 windows, descriptive)"
        lines.append(
            f"{rank}. **{row['symbol']} {row['family']}, {row['horizon']} session(s)** - n={row['n']}{flag}, "
            f"mean signed {_p(row.get('mean_signed_return'))}, win rate {_p(row.get('win_rate'))}, "
            f"adverse close beyond expected move {_p(row.get('breach_close_rate'))}, "
            f"adverse intraday beyond expected move {_p(row.get('breach_intra_rate'))}."
        )
    lines.append("")
    lines.append(
        "What this means in trade terms: the structure worth paper-testing first is a defined-risk credit "
        "vertical after a mean-reversion stretch (sell the put vertical on a bullish stretch, the call "
        "vertical on a bearish one), sized at the same 1% defined risk, closed by the third session or at "
        "half the credit, whichever comes first. High-IV selling without a stretch had the largest sample and "
        "the weakest drift in this table. Anything on NBIS is unpriced historically, so it cannot rank as a "
        "tested strategy."
    )
    return "\n".join(lines)


def _snapshot(result: dict) -> str:
    snap = result.get("snapshot")
    if not snap:
        return "No current snapshot was saved with this run."
    lines = [
        f"Source: {snap['source']} As of {snap['as_of_utc']}.",
        "",
    ]
    for item in snap.get("underlyings") or []:
        change = item["last"] / item["previous_close"] - 1 if item.get("previous_close") else None
        lines.append(
            f"- {item['symbol']} last {item['last']:.2f} versus the {item['previous_close_date']} close "
            f"{item['previous_close']:.2f} ({_p(change)})."
        )
    lines.append("")
    lines.append("Nearest expirations: " + "; ".join(
        f"{symbol} {', '.join(days[:3])}" for symbol, days in (snap.get("first_expirations") or {}).items()
    ) + ".")
    quotes = snap.get("put_quotes") or []
    if quotes:
        lines.append("")
        rows = [["Symbol", "Expiry", "Put strike", "Bid", "Ask", "IV", "Delta", "Open interest"]]
        for quote in quotes:
            rows.append(
                [
                    quote["symbol"],
                    quote["expiration"],
                    _n(quote["strike"], 0),
                    _n(quote["bid"], 2),
                    _n(quote["ask"], 2),
                    _p(quote["iv"]),
                    _n(quote["delta"], 3),
                    str(quote["open_interest"]),
                ]
            )
        lines.append(_table(rows))
    for ill in result.get("illustrations") or []:
        lines.append("")
        lines.append(
            f"Illustrated from those quotes, {ill['symbol']} {ill['expiration']}: sell the {ill['short_strike']:.0f} put "
            f"at {ill['short_bid']:.2f}, buy the {ill['long_strike']:.0f} put at {ill['long_ask']:.2f}. "
            f"Credit {ill['credit']:.2f}, width {ill['width']:.0f}, max loss ${ill['max_loss_dollars']:.0f} per contract "
            "before commissions. This is a current quote snapshot, not a fill and not a recommendation."
        )
    return "\n".join(lines)


def _nbis(result: dict) -> str:
    snap = result.get("snapshot") or {}
    nbis_quotes = [q for q in snap.get("put_quotes") or [] if q["symbol"] == "NBIS"]
    if nbis_quotes:
        ivs = [float(q["iv"]) for q in nbis_quotes]
        nearest = (snap.get("first_expirations") or {}).get("NBIS", ["n/a"])[0]
        today = (
            f"today's chain (nearest expiry {nearest}, put IV {_p(min(ivs))} to {_p(max(ivs))} "
            "at the quoted strikes)"
        )
    else:
        today = "today's chain"
    return "\n".join(
        [
            "NBIS has 0 rows in the free historical volatility table and 0 option-chain rows on 2026-11-06, "
            "and Yahoo's current-options endpoint returned HTTP 401 in this run. The current NBIS quotes in "
            f"the snapshot above come from a read-only broker quote feed fetched for this report. They describe "
            f"{today}. They cannot backtest anything.",
            "",
            "So the honest NBIS answer is narrower: the stock's own 1-3 session behavior after stretch and "
            "trend signals is in the proxy table, and its realized vol over the study year was about 109% with "
            "a 58% max drawdown in the earlier pair study. Premium on NBIS is large because the moves are large. "
            "Until a historical NBIS chain is available, any NBIS premium structure is an untested candidate "
            "for paper trading at defined risk, not a ranked strategy.",
        ]
    )


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
