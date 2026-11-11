"""Live (delayed) option chain check from CBOE's free delayed-quotes file.

This is a current snapshot, not a backtest. It answers one beginner question:
does today's chain offer a small, defined-risk premium trade that resembles
the patterns tested in this repo, and what would its max loss be?
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

from oppfinder.data_sources import fetch_json

CBOE_CHAIN_URL = "https://cdn.cboe.com/api/global/delayed_quotes/options/{symbol}.json"
_OCC = re.compile(r"(\d{6})([CP])(\d{8})$")


def parse_occ(code: str) -> tuple[date, str, float] | None:
    match = _OCC.search(code or "")
    if not match:
        return None
    yymmdd, right, strike = match.groups()
    try:
        expiry = date(2000 + int(yymmdd[:2]), int(yymmdd[2:4]), int(yymmdd[4:6]))
    except ValueError:
        return None
    return expiry, ("CALL" if right == "C" else "PUT"), int(strike) / 1000.0


def parse_cboe_chain(payload: dict, symbol: str) -> dict:
    data = payload.get("data") or {}
    options = []
    for item in data.get("options") or []:
        parsed = parse_occ(str(item.get("option") or ""))
        if parsed is None:
            continue
        expiry, right, strike = parsed
        options.append(
            {
                "expiration": expiry.isoformat(),
                "type": right,
                "strike": strike,
                "bid": _float(item.get("bid")),
                "ask": _float(item.get("ask")),
                "iv": _float(item.get("iv")),
                "delta": _float(item.get("delta")),
                "open_interest": _float(item.get("open_interest")),
                "volume": _float(item.get("volume")),
            }
        )
    expirations = sorted({row["expiration"] for row in options})
    return {
        "symbol": symbol,
        "timestamp": payload.get("timestamp"),
        "current_price": _float(data.get("current_price")),
        "price_change_percent": _float(data.get("price_change_percent")),
        "prev_day_close": _float(data.get("prev_day_close")),
        "iv30_percent": _float(data.get("iv30")),
        "expirations": expirations,
        "options": options,
    }


def pick_expiry(expirations: list[str], today: date) -> str | None:
    """First expiry at least one day out, so the trade is not expiring today."""
    for expiry in expirations:
        if date.fromisoformat(expiry) > today:
            return expiry
    return expirations[-1] if expirations else None


def build_credit_candidate(options: list[dict], expiration: str, right: str) -> dict | None:
    """Short leg nearest a 0.30 delta, next strike as the wing. Defined risk only."""
    legs = [
        row
        for row in options
        if row["expiration"] == expiration and row["type"] == right and _valid(row) and row.get("delta") is not None
    ]
    if not legs:
        return None
    target = -0.30 if right == "PUT" else 0.30
    short = min(legs, key=lambda row: abs(float(row["delta"]) - target))
    strikes = sorted({float(row["strike"]) for row in legs})
    # Protective leg about 5 points away, matching the tested illustrations.
    # On a sparse grid that is simply the next strike.
    if right == "PUT":
        lower = [strike for strike in strikes if strike < float(short["strike"])]
        if not lower:
            return None
        wing_strike = min(lower, key=lambda strike: abs(strike - (float(short["strike"]) - 5.0)))
    else:
        higher = [strike for strike in strikes if strike > float(short["strike"])]
        if not higher:
            return None
        wing_strike = min(higher, key=lambda strike: abs(strike - (float(short["strike"]) + 5.0)))
    wing = next(row for row in legs if float(row["strike"]) == wing_strike)
    credit = float(short["bid"]) - float(wing["ask"])
    width = abs(float(short["strike"]) - wing_strike)
    if credit <= 0 or width <= 0:
        return None
    max_loss = (width - credit) * 100
    breakeven = float(short["strike"]) - credit if right == "PUT" else float(short["strike"]) + credit
    return {
        "right": right,
        "expiration": expiration,
        "short_strike": float(short["strike"]),
        "long_strike": wing_strike,
        "short_bid": float(short["bid"]),
        "long_ask": float(wing["ask"]),
        "short_delta": float(short["delta"]),
        "short_iv": short.get("iv"),
        "credit": credit,
        "width": width,
        "max_loss_dollars": max_loss,
        "max_profit_dollars": credit * 100,
        "breakeven": breakeven,
    }


def pattern_checks(context: dict, candidate: dict | None, iv30_percent: float | None, spot: float | None) -> list[dict]:
    """Plain-language checks. `context` is the last completed daily bar's indicators."""
    checks = []
    rv = context.get("rv20")
    if iv30_percent is not None and rv:
        checks.append(
            {
                "id": "expensive",
                "label": "Are the options expensive?",
                "pass": iv30_percent / 100.0 > float(rv),
                "detail": (
                    f"Option market is charging about {iv30_percent:.0f}% expected movement. "
                    f"This stock actually moved about {float(rv) * 100:.0f}% a year pace over the last 20 days. "
                    "Selling premium only makes sense when the price charged is higher than the movement that usually happens."
                ),
            }
        )
    signals = context.get("signals") or {}
    if candidate is not None:
        want = 1 if candidate["right"] == "PUT" else -1
        stretched = signals.get("mr_fade") == want
        checks.append(
            {
                "id": "stretched",
                "label": "Did the stock just get stretched? (our best-tested pattern)",
                "pass": stretched,
                "detail": (
                    "Our tests liked selling premium right after a stretch, because stretched moves often calm down. "
                    + (
                        "The last finished trading day did show that stretch."
                        if stretched
                        else "The last finished trading day did not show that stretch, so this would not be our tested pattern."
                    )
                ),
            }
        )
        sma50 = context.get("sma50")
        if spot is not None and sma50:
            with_trend = spot > float(sma50) if candidate["right"] == "PUT" else spot < float(sma50)
            checks.append(
                {
                    "id": "trend",
                    "label": "Is the trade on the calm side of the trend?",
                    "pass": with_trend,
                    "detail": (
                        f"Price now {spot:.2f}, 50-day average {float(sma50):.2f}. "
                        "A put-credit trade wants price above that average; a call-credit trade wants it below."
                    ),
                }
            )
        checks.append(
            {
                "id": "risk",
                "label": "Is the worst case small and known?",
                "pass": candidate["max_loss_dollars"] <= 1000,
                "detail": (
                    f"Worst case on 1 contract is ${candidate['max_loss_dollars']:.0f} if everything goes wrong. "
                    f"You collect ${candidate['max_profit_dollars']:.0f} if you close flat. "
                    "Never sell options without that protective second leg."
                ),
            }
        )
        checks.append(
            {
                "id": "distance",
                "label": "Is the strike a reasonable distance away?",
                "pass": abs(candidate["short_delta"]) <= 0.35,
                "detail": (
                    f"The sold option's delta is {candidate['short_delta']:.2f}. "
                    "Roughly, traders read 0.30 as about a 30% chance of ending in the money. "
                    "Much closer than that is gambling, not premium collecting."
                ),
            }
        )
    return checks


def verdict(checks: list[dict]) -> str:
    if not checks:
        return "No check could be run."
    passed = sum(1 for check in checks if check["pass"])
    if passed == len(checks):
        return "This matches our tested pattern."
    if passed >= len(checks) - 1:
        return "This partly matches. Read the failed check before doing anything."
    return "This does not match our tested pattern."


def fetch_live(symbol: str) -> dict:
    payload, err = fetch_json(CBOE_CHAIN_URL.format(symbol=symbol), timeout=40, attempts=2)
    if err or not isinstance(payload, dict):
        raise RuntimeError(err or "empty chain payload")
    return parse_cboe_chain(payload, symbol)


def build_live(contexts: dict[str, dict], symbols: tuple[str, ...] = ("SPY", "NBIS")) -> dict:
    out = {"source": "CBOE delayed quotes (free, delayed; not a trade fill)", "symbols": {}}
    for symbol in symbols:
        try:
            chain = fetch_live(symbol)
        except Exception as exc:
            out["symbols"][symbol] = {"error": f"{type(exc).__name__}: {exc}"}
            continue
        today = date.fromisoformat(str(chain["timestamp"])[:10]) if chain.get("timestamp") else date.today()
        expiry = pick_expiry(chain["expirations"], today)
        entry = {
            "timestamp": chain["timestamp"],
            "current_price": chain["current_price"],
            "price_change_percent": chain["price_change_percent"],
            "prev_day_close": chain["prev_day_close"],
            "iv30_percent": chain["iv30_percent"],
            "expiry_used": expiry,
            "candidates": {},
        }
        context = contexts.get(symbol) or {}
        for right in ("PUT", "CALL"):
            candidate = build_credit_candidate(chain["options"], expiry, right) if expiry else None
            entry["candidates"][right] = candidate
            if candidate is not None:
                checks = pattern_checks(context, candidate, chain["iv30_percent"], chain["current_price"])
                candidate["checks"] = checks
                candidate["verdict"] = verdict(checks)
        # keep only near-money rows for the fallback file so it stays small
        spot = chain["current_price"] or 0
        near = [
            row
            for row in chain["options"]
            if row["expiration"] == expiry and spot and abs(row["strike"] - spot) / spot <= 0.15
        ]
        near.sort(key=lambda row: abs(row["strike"] - spot))
        entry["near_options"] = sorted(near[:12], key=lambda row: row["strike"])
        out["symbols"][symbol] = entry
    return out


def _valid(row: dict) -> bool:
    bid = row.get("bid")
    ask = row.get("ask")
    return bid is not None and ask is not None and float(bid) > 0 and float(ask) >= float(bid)


def _float(value) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch delayed CBOE chains and write ui/live.json.")
    parser.add_argument("--data", type=Path, default=Path("ui/data.json"), help="UI data file with symbol context.")
    parser.add_argument("--out", type=Path, default=Path("ui/live.json"))
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    data_path = args.data if args.data.is_absolute() else root / args.data
    contexts = {}
    if data_path.exists():
        contexts = (json.loads(data_path.read_text()).get("symbol_context") or {})
    live = build_live(contexts)
    out = args.out if args.out.is_absolute() else root / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(live, indent=1))
    print(f"wrote {out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
