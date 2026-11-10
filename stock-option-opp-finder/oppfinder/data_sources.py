"""Download and parse public prices, CBOE index vol, and DoltHub option quotes."""

from __future__ import annotations

import csv
import json
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from oppfinder.config import (
    CBOE_EQUITY_PC_URL,
    CBOE_INDEX_URL,
    CBOE_TOTAL_PC_URL,
    CNN_FEAR_GREED_URL,
    DOLT_SQL_URL,
    GDELT_TONE_URL,
    USER_AGENT,
    YAHOO_CHART_URL,
)
from oppfinder.spreads import ChainRow, parse_chain_row

NY = ZoneInfo("America/New_York")
_SYMBOL = re.compile(r"^[A-Z]{1,5}$")
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass(frozen=True)
class Split:
    ex_date: date
    numerator: float
    denominator: float


def subsequent_split_factor(bar_date: date, splits: list[Split]) -> float:
    """Undo later split adjustments so the result is the price that traded that day.

    A 10-for-1 split is numerator 10, denominator 1. Yahoo's historical quote is
    divided by that ratio, so bars before the ex-date are multiplied back by 10.
    """
    factor = 1.0
    for split in splits:
        if bar_date < split.ex_date:
            if split.denominator == 0:
                raise ValueError("split denominator is 0")
            factor *= split.numerator / split.denominator
    return factor


def parse_cboe_index_csv(text: str) -> list[dict]:
    rows: list[dict] = []
    for line in text.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 5:
            continue
        try:
            day = datetime.strptime(parts[0], "%m/%d/%Y").date()
            rows.append(
                {
                    "date": day,
                    "open": float(parts[1]),
                    "high": float(parts[2]),
                    "low": float(parts[3]),
                    "close": float(parts[4]),
                }
            )
        except ValueError:
            continue
    rows.sort(key=lambda row: row["date"])
    return rows


def parse_put_call_csv(text: str) -> list[dict]:
    rows: list[dict] = []
    for line in text.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 5:
            continue
        try:
            day = datetime.strptime(parts[0], "%m/%d/%Y").date()
            rows.append({"date": day, "put_call": float(parts[4])})
        except ValueError:
            continue
    rows.sort(key=lambda row: row["date"])
    return rows


def parse_yahoo_chart(payload: dict) -> tuple[list[dict], list[Split]]:
    chart = payload.get("chart") or {}
    if chart.get("error"):
        raise ValueError(str(chart["error"]))
    result = (chart.get("result") or [None])[0]
    if not result or not result.get("timestamp"):
        raise ValueError("yahoo chart result was empty")
    quote = ((result.get("indicators") or {}).get("quote") or [{}])[0]
    opens = quote.get("open") or []
    highs = quote.get("high") or []
    lows = quote.get("low") or []
    closes = quote.get("close") or []
    volumes = quote.get("volume") or []
    splits = _parse_splits(result)
    bars: list[dict] = []
    for i, raw_ts in enumerate(result["timestamp"]):
        if i >= len(closes) or None in (opens[i], highs[i], lows[i], closes[i], volumes[i]):
            continue
        day = datetime.fromtimestamp(int(raw_ts), NY).date()
        close = float(closes[i])
        factor = subsequent_split_factor(day, splits)
        bars.append(
            {
                "date": day,
                "open": float(opens[i]),
                "high": float(highs[i]),
                "low": float(lows[i]),
                "close": close,
                "volume": float(volumes[i]),
                "raw_close": close * factor,
            }
        )
    dedup: dict[date, dict] = {}
    for bar in bars:
        dedup[bar["date"]] = bar
    return [dedup[day] for day in sorted(dedup)], splits


def _parse_splits(result: dict) -> list[Split]:
    raw = ((result.get("events") or {}).get("splits") or {})
    if not isinstance(raw, dict):
        return []
    splits: list[Split] = []
    for key, item in raw.items():
        when = int(item.get("date") or key)
        ex_date = datetime.fromtimestamp(when, NY).date()
        splits.append(
            Split(
                ex_date=ex_date,
                numerator=float(item["numerator"]),
                denominator=float(item["denominator"]),
            )
        )
    splits.sort(key=lambda split: split.ex_date)
    return splits


def extract_gdelt_tone(payload: dict) -> list[tuple[date, float]] | None:
    """Parse a GDELT timelinetone payload. Return None if the shape is not the documented one."""
    timeline = payload.get("timeline")
    if not isinstance(timeline, list):
        return None
    for series in timeline:
        if not isinstance(series, dict) or not isinstance(series.get("data"), list):
            continue
        points: list[tuple[date, float]] = []
        for item in series["data"]:
            if not isinstance(item, dict) or "date" not in item or "value" not in item:
                return None
            try:
                day = datetime.strptime(str(item["date"])[:8], "%Y%m%d").date()
                points.append((day, float(item["value"])))
            except (TypeError, ValueError):
                return None
        if points:
            return points
    return None


def extract_cnn_fear_greed(payload: dict) -> list[tuple[date, float]] | None:
    """Parse CNN's historical fear-and-greed object. Any other shape returns None."""
    hist = payload.get("fear_and_greed_historical")
    if not isinstance(hist, dict) or not isinstance(hist.get("data"), list):
        return None
    points: list[tuple[date, float]] = []
    for item in hist["data"]:
        if not isinstance(item, dict) or "x" not in item or "y" not in item:
            return None
        try:
            day = datetime.fromtimestamp(float(item["x"]) / 1000, NY).date()
            points.append((day, float(item["y"])))
        except (TypeError, ValueError, OSError):
            return None
    return points or None


def month_windows(start: date, end: date) -> list[tuple[date, date]]:
    windows: list[tuple[date, date]] = []
    cursor = date(start.year, start.month, 1)
    while cursor <= end:
        if cursor.month == 12:
            nxt = date(cursor.year + 1, 1, 1)
        else:
            nxt = date(cursor.year, cursor.month + 1, 1)
        windows.append((cursor, nxt))
        cursor = nxt
    return windows


def _request(url: str, timeout: int) -> tuple[int | None, bytes | None, str | None]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status, response.read(), None
    except urllib.error.HTTPError as exc:
        return exc.code, None, f"HTTP {exc.code}: {exc.reason}"
    except Exception as exc:
        return None, None, f"{type(exc).__name__}: {exc}"


def fetch_text(url: str, timeout: int = 60, attempts: int = 3) -> tuple[str | None, str | None]:
    last = "no attempt"
    for attempt in range(attempts):
        status, body, err = _request(url, timeout)
        if err is None and body is not None and status == 200:
            return body.decode("utf-8", errors="replace"), None
        last = err or f"HTTP {status}"
        time.sleep(2 ** attempt)
    return None, last


def fetch_json(url: str, timeout: int = 60, attempts: int = 3) -> tuple[dict | list | None, str | None]:
    text, err = fetch_text(url, timeout=timeout, attempts=attempts)
    if text is None:
        return None, err
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, f"JSONDecodeError: {exc}"
    if isinstance(parsed, (dict, list)):
        return parsed, None
    return None, "JSON root was not an object or list"


def dolt_query(sql: str, attempts: int = 3, timeout: int = 50) -> tuple[list[dict] | None, str | None]:
    url = DOLT_SQL_URL + "?" + urllib.parse.urlencode({"q": sql})
    last = "no attempt"
    for attempt in range(attempts):
        payload, err = fetch_json(url, timeout=timeout, attempts=1)
        if err or not isinstance(payload, dict):
            last = err or "empty dolt payload"
        elif payload.get("query_execution_status") != "Success":
            last = str(payload.get("query_execution_message") or payload.get("query_execution_status"))
        else:
            rows = payload.get("rows") or []
            if not isinstance(rows, list):
                return None, "dolt rows were not a list"
            return rows, None
        time.sleep(2 ** attempt)
    return None, last


def _check_symbol(symbol: str) -> str:
    if not _SYMBOL.match(symbol):
        raise ValueError(f"refusing symbol {symbol!r}")
    return symbol


def _check_date(day: date) -> str:
    text = day.isoformat()
    if not _ISO_DATE.match(text):
        raise ValueError(text)
    return text


class ResearchStore:
    """File cache so a rerun does not repeat calls that already succeeded."""

    def __init__(self, root: Path, refresh: bool = False) -> None:
        self.root = root
        self.refresh = refresh
        self.errors: list[dict] = []
        self.chain_counts = {"ok": 0, "empty": 0, "error": 0, "cache": 0}
        self._lock = threading.Lock()
        self._path_locks: dict[str, threading.Lock] = {}

    def note(self, source: str, detail: str, symbol: str | None = None) -> None:
        with self._lock:
            self.errors.append({"source": source, "symbol": symbol, "detail": detail})

    def _path_lock(self, path: Path) -> threading.Lock:
        key = str(path)
        with self._lock:
            if key not in self._path_locks:
                self._path_locks[key] = threading.Lock()
            return self._path_locks[key]

    def load_prices(self, symbol: str, start: date, end: date) -> tuple[list[dict], list[Split]]:
        symbol = _check_symbol(symbol)
        path = self.root / "prices" / f"{symbol}.json"
        if path.exists() and not self.refresh:
            payload = json.loads(path.read_text())
            splits = [
                Split(
                    ex_date=date.fromisoformat(item["ex_date"]),
                    numerator=float(item["numerator"]),
                    denominator=float(item["denominator"]),
                )
                for item in payload["splits"]
            ]
            return _restore_bar_dates(payload["bars"]), splits
        start_ts = int(datetime.combine(start, datetime.min.time(), NY).timestamp())
        end_ts = int(datetime.combine(end + timedelta(days=2), datetime.min.time(), NY).timestamp())
        url = YAHOO_CHART_URL.format(symbol=symbol, start=start_ts, end=end_ts)
        payload, err = fetch_json(url, timeout=60, attempts=3)
        if err or not isinstance(payload, dict):
            self.note("yahoo", err or "empty payload", symbol)
            return [], []
        try:
            bars, splits = parse_yahoo_chart(payload)
        except (KeyError, ValueError, TypeError) as exc:
            self.note("yahoo", f"{type(exc).__name__}: {exc}", symbol)
            return [], []
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "bars": [{**bar, "date": bar["date"].isoformat()} for bar in bars],
                    "splits": [
                        {
                            "ex_date": split.ex_date.isoformat(),
                            "numerator": split.numerator,
                            "denominator": split.denominator,
                        }
                        for split in splits
                    ],
                }
            )
        )
        return bars, splits

    def load_index(self, name: str) -> list[dict]:
        if not re.match(r"^[A-Z0-9]{2,6}$", name):
            raise ValueError(name)
        path = self.root / "index_vol" / f"{name}.csv"
        if path.exists() and not self.refresh:
            return _read_index_csv(path)
        url = CBOE_INDEX_URL.format(name=name)
        text, err = fetch_text(url, timeout=60, attempts=3)
        if text is None:
            self.note("cboe", err or "empty", name)
            return []
        rows = parse_cboe_index_csv(text)
        if not rows:
            self.note("cboe", "parsed zero rows", name)
            return []
        _write_index_csv(path, rows)
        return rows

    def load_volatility(self, symbol: str, start: date, end: date) -> list[dict]:
        symbol = _check_symbol(symbol)
        rows: list[dict] = []
        for lo, hi in month_windows(start, end):
            month_rows, err = self._vol_month(symbol, lo, hi)
            if err:
                self.note("dolthub_vol", f"{lo.isoformat()} {err}", symbol)
                continue
            rows.extend(month_rows)
        dedup = {row["date"]: row for row in rows}
        return [dedup[day] for day in sorted(dedup)]

    def _vol_month(self, symbol: str, lo: date, hi: date) -> tuple[list[dict], str | None]:
        path = self.root / "vol_cache" / symbol / f"{lo.isoformat()}.json"
        if path.exists() and not self.refresh:
            payload = json.loads(path.read_text())
            return [_restore_vol(row) for row in payload], None
        sql = (
            "SELECT date, act_symbol, iv_current, hv_current, iv_year_high, iv_year_low "
            "FROM volatility_history "
            f"WHERE act_symbol = '{symbol}' AND date >= '{_check_date(lo)}' AND date < '{_check_date(hi)}'"
        )
        raw, err = dolt_query(sql, attempts=2, timeout=40)
        if err or raw is None:
            return [], err or "empty"
        parsed = []
        for row in raw:
            try:
                parsed.append(
                    {
                        "date": date.fromisoformat(str(row["date"])[:10]),
                        "symbol": symbol,
                        "iv_current": _float_or_none(row.get("iv_current")),
                        "hv_current": _float_or_none(row.get("hv_current")),
                        "iv_year_high": _float_or_none(row.get("iv_year_high")),
                        "iv_year_low": _float_or_none(row.get("iv_year_low")),
                    }
                )
            except (KeyError, ValueError):
                continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps([{**row, "date": row["date"].isoformat()} for row in parsed]))
        return parsed, None

    def load_chain(self, symbol: str, day: date) -> tuple[str, list[ChainRow]]:
        symbol = _check_symbol(symbol)
        path = self.root / "chains" / symbol / f"{day.isoformat()}.csv"
        lock = self._path_lock(path)
        with lock:
            if path.exists() and not self.refresh:
                rows = _read_chain(path)
                with self._lock:
                    self.chain_counts["cache"] += 1
                    self.chain_counts["ok" if rows else "empty"] += 1
                return ("ok" if rows else "empty"), rows
            sql = (
                "SELECT date, expiration, strike, call_put, bid, ask, vol, delta "
                "FROM option_chain "
                f"WHERE act_symbol = '{symbol}' AND date = '{_check_date(day)}'"
            )
            raw, err = dolt_query(sql, attempts=3, timeout=40)
            if err or raw is None:
                self.note("dolthub_chain", err or "empty", f"{symbol} {day.isoformat()}")
                with self._lock:
                    self.chain_counts["error"] += 1
                return "error", []
            parsed = [row for row in (parse_chain_row(item) for item in raw) if row is not None]
            if raw and not parsed:
                self.note("dolthub_chain", f"{len(raw)} rows failed to parse", f"{symbol} {day.isoformat()}")
            _write_chain(path, parsed)
            status = "ok" if parsed else "empty"
            with self._lock:
                self.chain_counts[status] += 1
            return status, parsed


def _restore_bar_dates(bars: list[dict]) -> list[dict]:
    restored = []
    for bar in bars:
        row = dict(bar)
        if isinstance(row["date"], str):
            row["date"] = date.fromisoformat(row["date"])
        restored.append(row)
    return restored


def _restore_vol(row: dict) -> dict:
    item = dict(row)
    if isinstance(item["date"], str):
        item["date"] = date.fromisoformat(item["date"])
    return item


def _float_or_none(value: object) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _write_index_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["date", "open", "high", "low", "close"])
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "date": row["date"].isoformat()})


def _read_index_csv(path: Path) -> list[dict]:
    with path.open() as handle:
        return [
            {
                "date": date.fromisoformat(row["date"]),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
            }
            for row in csv.DictReader(handle)
        ]


def _write_chain(path: Path, rows: list[ChainRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["date", "expiration", "strike", "call_put", "bid", "ask", "vol", "delta"])
        for row in rows:
            writer.writerow(
                [
                    "",
                    row.expiration.isoformat(),
                    format(row.strike, "f"),
                    row.call_put,
                    format(row.bid, "f"),
                    format(row.ask, "f"),
                    "" if row.iv is None else format(row.iv, "f"),
                    "" if row.delta is None else format(row.delta, "f"),
                ]
            )


def _read_chain(path: Path) -> list[ChainRow]:
    rows: list[ChainRow] = []
    with path.open() as handle:
        for item in csv.DictReader(handle):
            parsed = parse_chain_row(item)
            if parsed is not None:
                rows.append(parsed)
    return rows


def probe_sentiment() -> dict:
    """Try free sentiment sources. Never fill a score when the call or the file fails."""
    attempts: list[dict] = []
    gdelt_points = None
    payload, err = fetch_json(GDELT_TONE_URL, timeout=40, attempts=1)
    if err or not isinstance(payload, dict):
        attempts.append({"source": "GDELT DOC timelinetone", "url": GDELT_TONE_URL, "result": err or "not a JSON object"})
    else:
        gdelt_points = extract_gdelt_tone(payload)
        if gdelt_points is None:
            attempts.append(
                {
                    "source": "GDELT DOC timelinetone",
                    "url": GDELT_TONE_URL,
                    "result": f"schema not recognized; top-level keys={sorted(payload.keys())}",
                }
            )
        else:
            attempts.append(
                {
                    "source": "GDELT DOC timelinetone",
                    "url": GDELT_TONE_URL,
                    "result": f"parsed {len(gdelt_points)} tone points",
                    "used_candidate": True,
                }
            )
    cnn_points = None
    payload, err = fetch_json(CNN_FEAR_GREED_URL, timeout=40, attempts=1)
    if err or not isinstance(payload, dict):
        attempts.append({"source": "CNN Fear and Greed", "url": CNN_FEAR_GREED_URL, "result": err or "not a JSON object"})
    else:
        cnn_points = extract_cnn_fear_greed(payload)
        if cnn_points is None:
            attempts.append(
                {
                    "source": "CNN Fear and Greed",
                    "url": CNN_FEAR_GREED_URL,
                    "result": f"schema not recognized; top-level keys={sorted(payload.keys())}",
                }
            )
        else:
            attempts.append(
                {
                    "source": "CNN Fear and Greed",
                    "url": CNN_FEAR_GREED_URL,
                    "result": f"parsed {len(cnn_points)} points",
                    "used_candidate": True,
                }
            )
    equity_put_call: list[dict] = []
    for name, url in (("CBOE equity put/call", CBOE_EQUITY_PC_URL), ("CBOE total put/call", CBOE_TOTAL_PC_URL)):
        text, err = fetch_text(url, timeout=40, attempts=1)
        if text is None:
            attempts.append({"source": name, "url": url, "result": err or "empty"})
            continue
        rows = parse_put_call_csv(text)
        if not rows:
            attempts.append({"source": name, "url": url, "result": "parsed zero dated rows"})
            continue
        last = rows[-1]["date"].isoformat()
        attempts.append(
            {
                "source": name,
                "url": url,
                "result": f"file downloaded; last date {last}. Not used unless that date reaches the study.",
                "last_date": last,
                "n": len(rows),
            }
        )
        if name == "CBOE equity put/call":
            equity_put_call = rows
    return {"attempts": attempts, "gdelt": gdelt_points, "cnn": cnn_points, "equity_put_call": equity_put_call}
