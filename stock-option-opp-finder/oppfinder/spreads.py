"""One-strike verticals from a real chain snapshot. No modeled premiums."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation

from oppfinder.config import (
    CREDIT_DELTA_TOLERANCE,
    CREDIT_SHORT_DELTA,
    DEBIT_DELTA_TOLERANCE,
    DEBIT_LONG_DELTA,
    EQUITY0,
    MAX_CREDIT_TO_WIDTH,
    MAX_DEBIT_TO_WIDTH,
    MAX_ONE_LOT_RISK_FRAC,
    MAX_REL_QUOTE_SPREAD,
    MAX_SPOT_ATM_GAP,
    OPTION_COMMISSION,
    RISK_FRAC,
)


@dataclass(frozen=True)
class ChainRow:
    expiration: date
    strike: Decimal
    call_put: str
    bid: Decimal
    ask: Decimal
    iv: Decimal | None
    delta: Decimal | None


@dataclass(frozen=True)
class Spread:
    kind: str
    right: str
    expiration: date
    long_strike: Decimal
    short_strike: Decimal
    long_delta: Decimal | None
    short_delta: Decimal | None
    premium: Decimal
    width: Decimal
    max_loss: Decimal
    max_profit: Decimal
    short_iv: Decimal | None


def parse_chain_row(row: dict) -> ChainRow | None:
    try:
        expiration = date.fromisoformat(str(row["expiration"])[:10])
        strike = Decimal(str(row["strike"]))
        right = str(row["call_put"]).strip().upper()
        if right not in ("CALL", "PUT"):
            return None
        bid = _decimal(row.get("bid"))
        ask = _decimal(row.get("ask"))
        if bid is None or ask is None:
            return None
        return ChainRow(
            expiration=expiration,
            strike=strike,
            call_put=right,
            bid=bid,
            ask=ask,
            iv=_decimal(row.get("vol")),
            delta=_decimal(row.get("delta")),
        )
    except (KeyError, ValueError, InvalidOperation):
        return None


def _decimal(value: object) -> Decimal | None:
    if value is None or value == "":
        return None
    return Decimal(str(value))


def valid_quote(row: ChainRow, max_rel: Decimal = MAX_REL_QUOTE_SPREAD) -> bool:
    if row.bid <= 0 or row.ask < row.bid:
        return False
    mid = (row.bid + row.ask) / 2
    if mid <= 0:
        return False
    return (row.ask - row.bid) / mid <= max_rel


def pick_expiration(
    expirations: list[date],
    trade_date: date,
    target_dte: int,
    min_dte: int,
    max_dte: int,
) -> date | None:
    choices: list[tuple[int, int, date]] = []
    for expiration in set(expirations):
        dte = (expiration - trade_date).days
        if min_dte <= dte <= max_dte:
            choices.append((abs(dte - target_dte), -dte, expiration))
    if not choices:
        return None
    choices.sort()
    return choices[0][2]


def closest_delta(rows: list[ChainRow], target: Decimal, tolerance: Decimal) -> ChainRow | None:
    pool = [
        row
        for row in rows
        if row.delta is not None and valid_quote(row) and abs(row.delta - target) <= tolerance
    ]
    if not pool:
        return None
    return min(pool, key=lambda row: (abs((row.delta or Decimal(0)) - target), row.strike))


def adjacent_otm_strike(strikes: list[Decimal], strike: Decimal, right: str) -> Decimal | None:
    if right == "CALL":
        higher = [item for item in strikes if item > strike]
        return min(higher) if higher else None
    if right == "PUT":
        lower = [item for item in strikes if item < strike]
        return max(lower) if lower else None
    raise ValueError(right)


def _wing(legs: list[ChainRow], anchor: Decimal, right: str) -> ChainRow | None:
    quoted = [row for row in legs if valid_quote(row)]
    wing_strike = adjacent_otm_strike([row.strike for row in quoted], anchor, right)
    if wing_strike is None:
        return None
    matches = [row for row in quoted if row.strike == wing_strike]
    if len(matches) != 1:
        return None
    return matches[0]


def build_debit_vertical(
    rows: list[ChainRow],
    trade_date: date,
    right: str,
    dte: tuple[int, int, int],
) -> tuple[Spread | None, str]:
    if right not in ("CALL", "PUT"):
        raise ValueError(right)
    target, min_dte, max_dte = dte
    expiration = pick_expiration([row.expiration for row in rows], trade_date, target, min_dte, max_dte)
    if expiration is None:
        return None, "no_expiration"
    legs = [row for row in rows if row.expiration == expiration and row.call_put == right]
    long_target = DEBIT_LONG_DELTA if right == "CALL" else -DEBIT_LONG_DELTA
    long_leg = closest_delta(legs, long_target, DEBIT_DELTA_TOLERANCE)
    if long_leg is None:
        return None, "no_long_leg"
    short_leg = _wing(legs, long_leg.strike, right)
    if short_leg is None:
        return None, "no_wing"
    if long_leg.delta is not None and short_leg.delta is not None:
        if right == "CALL" and short_leg.delta > long_leg.delta:
            return None, "wing_not_otm"
        if right == "PUT" and short_leg.delta < long_leg.delta:
            return None, "wing_not_otm"
    debit = long_leg.ask - short_leg.bid
    width = abs(short_leg.strike - long_leg.strike)
    if debit <= 0:
        return None, "nonpositive_debit"
    if width <= debit:
        return None, "no_max_profit"
    if debit / width > MAX_DEBIT_TO_WIDTH:
        return None, "debit_too_wide"
    return (
        Spread(
            kind="debit",
            right=right,
            expiration=expiration,
            long_strike=long_leg.strike,
            short_strike=short_leg.strike,
            long_delta=long_leg.delta,
            short_delta=short_leg.delta,
            premium=debit,
            width=width,
            max_loss=debit,
            max_profit=width - debit,
            short_iv=short_leg.iv,
        ),
        "ok",
    )


def build_credit_vertical(
    rows: list[ChainRow],
    spot: Decimal,
    trade_date: date,
    right: str,
    dte: tuple[int, int, int],
) -> tuple[Spread | None, str]:
    if right not in ("CALL", "PUT"):
        raise ValueError(right)
    target, min_dte, max_dte = dte
    expiration = pick_expiration([row.expiration for row in rows], trade_date, target, min_dte, max_dte)
    if expiration is None:
        return None, "no_expiration"
    legs = [row for row in rows if row.expiration == expiration and row.call_put == right]
    short_target = -CREDIT_SHORT_DELTA if right == "PUT" else CREDIT_SHORT_DELTA
    short_leg = closest_delta(legs, short_target, CREDIT_DELTA_TOLERANCE)
    if short_leg is None:
        return None, "no_short_leg"
    if right == "PUT" and short_leg.strike >= spot:
        return None, "short_not_otm"
    if right == "CALL" and short_leg.strike <= spot:
        return None, "short_not_otm"
    long_leg = _wing(legs, short_leg.strike, right)
    if long_leg is None:
        return None, "no_wing"
    credit = short_leg.bid - long_leg.ask
    width = abs(short_leg.strike - long_leg.strike)
    if credit <= 0:
        return None, "nonpositive_credit"
    max_loss = width - credit
    if max_loss <= 0:
        return None, "nonpositive_max_loss"
    if width == 0 or credit / width > MAX_CREDIT_TO_WIDTH:
        return None, "credit_too_large"
    return (
        Spread(
            kind="credit",
            right=right,
            expiration=expiration,
            long_strike=long_leg.strike,
            short_strike=short_leg.strike,
            long_delta=long_leg.delta,
            short_delta=short_leg.delta,
            premium=credit,
            width=width,
            max_loss=max_loss,
            max_profit=credit,
            short_iv=short_leg.iv,
        ),
        "ok",
    )


def find_leg(
    rows: list[ChainRow],
    expiration: date,
    strike: Decimal,
    right: str,
) -> ChainRow | None:
    hits = [
        row
        for row in rows
        if row.expiration == expiration and row.strike == strike and row.call_put == right and valid_quote(row)
    ]
    if len(hits) != 1:
        return None
    return hits[0]


def option_pnl(spread: Spread, long_bid: Decimal, short_ask: Decimal, contracts: int) -> tuple[Decimal, Decimal]:
    if contracts < 1:
        raise ValueError("contracts")
    commission = OPTION_COMMISSION * 4 * contracts
    multiplier = Decimal(100) * contracts
    if spread.kind == "debit":
        exit_credit = long_bid - short_ask
        gross = (exit_credit - spread.premium) * multiplier
    elif spread.kind == "credit":
        exit_debit = short_ask - long_bid
        gross = (spread.premium - exit_debit) * multiplier
    else:
        raise ValueError(spread.kind)
    return gross - commission, commission


def size_contracts(max_loss_per_share: Decimal) -> int | None:
    risk_one = max_loss_per_share * Decimal(100) + OPTION_COMMISSION * 4
    budget = Decimal(str(EQUITY0 * RISK_FRAC))
    cap = Decimal(str(EQUITY0 * MAX_ONE_LOT_RISK_FRAC))
    if risk_one <= 0:
        return None
    count = int(budget // risk_one)
    if count >= 1:
        return count
    if risk_one <= cap:
        return 1
    return None


def atm_gap(rows: list[ChainRow], spot: Decimal, expiration: date) -> Decimal | None:
    if spot <= 0:
        return None
    pool = [
        row
        for row in rows
        if row.expiration == expiration and row.delta is not None and valid_quote(row)
    ]
    calls = [row for row in pool if row.call_put == "CALL"]
    puts = [row for row in pool if row.call_put == "PUT"]
    use = calls or puts
    if not use:
        return None
    target = Decimal("0.5") if use[0].call_put == "CALL" else Decimal("-0.5")
    atm = min(use, key=lambda row: (abs((row.delta or Decimal(0)) - target), row.strike))
    return abs(atm.strike - spot) / spot


def spot_matches(rows: list[ChainRow], spot: Decimal, expiration: date) -> bool:
    gap = atm_gap(rows, spot, expiration)
    return gap is not None and gap <= MAX_SPOT_ATM_GAP
