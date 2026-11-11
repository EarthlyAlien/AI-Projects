// Live check for one symbol: the stretch pattern on the last finished trading day,
// plus a defined-risk credit spread built from today's delayed chain.
// The indicator math mirrors oppfinder/indicators.py and oppfinder/signals.py;
// tests/test_js_parity.py checks that the two agree.

export const SYMBOLS = ["SPY", "NBIS"];
export const CHAIN_URL = (symbol) => `https://cdn-api.cboe.com/api/global/delayed_quotes/options/${symbol}.json`;
export const HISTORY_URL = (symbol) => `https://cdn-api.cboe.com/api/global/delayed_quotes/charts/historical/${symbol}.json`;

const RSI_LONG = 10;
const RSI_SHORT = 90;
const BAND_MULT = 2;
const SHORT_DELTA = 0.3;
const WING_POINTS = 5;
const MAX_LOSS_DOLLARS = 1000;
const MAX_SHORT_DELTA = 0.35;
// Same near-expiry window the 1-2 session backtest used: target 14 days, 5 to 25 allowed.
const DTE_TARGET = 14;
const DTE_MIN = 5;
const DTE_MAX = 25;

function mean(values) {
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function sampleStd(values) {
  const center = mean(values);
  return Math.sqrt(values.reduce((sum, value) => sum + (value - center) ** 2, 0) / (values.length - 1));
}

export function wilderRsi(closes, period) {
  if (closes.length <= period) return null;
  let gain = 0;
  let loss = 0;
  for (let i = 1; i <= period; i += 1) {
    const change = closes[i] - closes[i - 1];
    gain += Math.max(change, 0);
    loss += Math.max(-change, 0);
  }
  let avgGain = gain / period;
  let avgLoss = loss / period;
  const value = () => (avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss));
  let out = value();
  for (let i = period + 1; i < closes.length; i += 1) {
    const change = closes[i] - closes[i - 1];
    avgGain = (avgGain * (period - 1) + Math.max(change, 0)) / period;
    avgLoss = (avgLoss * (period - 1) + Math.max(-change, 0)) / period;
    out = value();
  }
  return out;
}

export function lastBarIndicators(closes) {
  const n = closes.length;
  const last = closes[n - 1];
  const window = (size) => (n >= size ? closes.slice(n - size) : null);
  const w20 = window(20);
  const w200 = window(200);
  let rv20 = null;
  if (n >= 21) {
    const logs = [];
    for (let i = n - 20; i < n; i += 1) logs.push(Math.log(closes[i] / closes[i - 1]));
    rv20 = sampleStd(logs) * Math.sqrt(252);
  }
  const sma20 = w20 ? mean(w20) : null;
  const std20 = w20 ? sampleStd(w20) : null;
  return {
    close: last,
    sma20,
    sma200: w200 ? mean(w200) : null,
    std20,
    lower_band: sma20 === null ? null : sma20 - BAND_MULT * std20,
    upper_band: sma20 === null ? null : sma20 + BAND_MULT * std20,
    rsi2: wilderRsi(closes, 2),
    rv20,
  };
}

export function stretchSide(ind) {
  const ok = (value) => value !== null && value !== undefined;
  if (![ind.close, ind.sma200, ind.rsi2, ind.lower_band, ind.upper_band].every(ok)) return 0;
  const down = ind.close > ind.sma200 && ind.rsi2 < RSI_LONG && ind.close < ind.lower_band;
  const up = ind.close < ind.sma200 && ind.rsi2 > RSI_SHORT && ind.close > ind.upper_band;
  if (down && !up) return 1;
  if (up && !down) return -1;
  return 0;
}

export function nyClock(now) {
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat("en-US", {
      timeZone: "America/New_York",
      year: "numeric", month: "2-digit", day: "2-digit",
      hour: "2-digit", minute: "2-digit", hourCycle: "h23",
    }).formatToParts(now).map((part) => [part.type, part.value])
  );
  return { date: `${parts.year}-${parts.month}-${parts.day}`, minutes: Number(parts.hour) * 60 + Number(parts.minute) };
}

export function finishedBars(history, now) {
  const clock = nyClock(now);
  return history.filter((bar) => !(bar.date === clock.date && clock.minutes < 16 * 60) && bar.date <= clock.date);
}

export function parseOcc(code) {
  const match = /(\d{6})([CP])(\d{8})$/.exec(code || "");
  if (!match) return null;
  const y = match[1];
  return {
    expiration: `20${y.slice(0, 2)}-${y.slice(2, 4)}-${y.slice(4, 6)}`,
    type: match[2] === "C" ? "CALL" : "PUT",
    strike: Number(match[3]) / 1000,
  };
}

export function parseChain(payload) {
  const data = (payload && payload.data) || {};
  const options = [];
  for (const item of data.options || []) {
    const parsed = parseOcc(item.option);
    if (!parsed) continue;
    options.push({ ...parsed, bid: item.bid, ask: item.ask, iv: item.iv, delta: item.delta, open_interest: item.open_interest });
  }
  return {
    timestamp: payload ? payload.timestamp : null,
    price: data.current_price ?? null,
    change_pct: data.price_change_percent ?? null,
    iv30_pct: data.iv30 ?? null,
    options,
  };
}

function daysBetween(fromIso, toIso) {
  return Math.round((Date.parse(`${toIso}T00:00:00Z`) - Date.parse(`${fromIso}T00:00:00Z`)) / 86400000);
}

export function pickExpiry(expirations, todayIso) {
  const choices = [...new Set(expirations)]
    .map((expiry) => ({ expiry, dte: daysBetween(todayIso, expiry) }))
    .filter((row) => row.dte >= DTE_MIN && row.dte <= DTE_MAX)
    .sort((a, b) => Math.abs(a.dte - DTE_TARGET) - Math.abs(b.dte - DTE_TARGET) || b.dte - a.dte);
  return choices.length ? choices[0] : null;
}

function quoted(row) {
  return row.bid > 0 && row.ask >= row.bid && row.delta !== null && row.delta !== undefined;
}

export function buildSpread(options, expiry, right) {
  const legs = options.filter((row) => row.expiration === expiry && row.type === right && quoted(row));
  if (!legs.length) return null;
  const target = right === "PUT" ? -SHORT_DELTA : SHORT_DELTA;
  const short = legs.reduce((best, row) => (Math.abs(row.delta - target) < Math.abs(best.delta - target) ? row : best));
  const beyond = [...new Set(legs.map((row) => row.strike))]
    .filter((strike) => (right === "PUT" ? strike < short.strike : strike > short.strike));
  if (!beyond.length) return null;
  const wingTarget = right === "PUT" ? short.strike - WING_POINTS : short.strike + WING_POINTS;
  const wingStrike = beyond.reduce((best, strike) => (Math.abs(strike - wingTarget) < Math.abs(best - wingTarget) ? strike : best));
  const wing = legs.find((row) => row.strike === wingStrike);
  const credit = Math.round((short.bid - wing.ask) * 100) / 100;
  const width = Math.abs(short.strike - wingStrike);
  if (credit <= 0 || width <= credit) return null;
  return {
    right,
    expiry,
    short_strike: short.strike,
    long_strike: wingStrike,
    short_bid: short.bid,
    long_ask: wing.ask,
    short_delta: short.delta,
    credit,
    width,
    max_profit: Math.round(credit * 100),
    max_loss: Math.round((width - credit) * 100),
    breakeven: right === "PUT" ? short.strike - credit : short.strike + credit,
    take_profit_debit: Math.floor((credit / 2) * 100) / 100,
  };
}

export function grade(stretch, trade, iv30Pct, rv20) {
  const checks = [];
  checks.push({
    id: "stretch",
    label: "Did the stock just make a big, fast move?",
    pass: stretch !== 0,
    detail: stretch === 1
      ? "Yes: a sharp drop while the long-term trend is up. Our tests liked selling right after this."
      : stretch === -1
        ? "Yes: a sharp jump while the long-term trend is down. Our tests liked selling right after this."
        : "No. The last finished day was a normal day, so the pattern we tested is not here.",
  });
  const expensive = iv30Pct !== null && rv20 !== null && iv30Pct / 100 > rv20;
  checks.push({
    id: "expensive",
    label: "Are options paying more than usual?",
    pass: expensive,
    detail: iv30Pct === null || rv20 === null
      ? "We could not read both numbers, so we count this as no."
      : `Options are priced for about ${iv30Pct.toFixed(0)}% movement a year. The stock really moved at about ${(rv20 * 100).toFixed(0)}% lately. ${expensive ? "So buyers are overpaying, which helps you." : "So you are not being paid extra."}`,
  });
  if (trade) {
    checks.push({
      id: "risk",
      label: "Is the worst case small and known?",
      pass: trade.max_loss <= MAX_LOSS_DOLLARS,
      detail: `Worst case is $${trade.max_loss} for one spread. Only trade if losing that would not hurt you.`,
    });
    checks.push({
      id: "distance",
      label: "Is the sold option far enough away?",
      pass: Math.abs(trade.short_delta) <= MAX_SHORT_DELTA,
      detail: `About a ${Math.round(Math.abs(trade.short_delta) * 100)}% chance it ends up in trouble at expiry, if nothing is done. You close long before that.`,
    });
  }
  let light = "red";
  if (stretch !== 0 && trade) light = checks.every((check) => check.pass) ? "green" : "yellow";
  return { checks, light };
}

export function analyze({ symbol, historyPayload, chainPayload, now }) {
  const history = ((historyPayload && historyPayload.data) || [])
    .filter((bar) => bar && typeof bar.close === "number" && bar.close > 0)
    .sort((a, b) => (a.date < b.date ? -1 : 1));
  const bars = finishedBars(history, now);
  const closes = bars.map((bar) => bar.close);
  const ind = closes.length ? lastBarIndicators(closes) : null;
  const stretch = ind ? stretchSide(ind) : 0;
  const chain = parseChain(chainPayload);
  const today = nyClock(now).date;
  const pick = pickExpiry(chain.options.map((row) => row.expiration), today);
  let direction = stretch === 1 ? "PUT" : stretch === -1 ? "CALL" : null;
  if (!direction && ind && ind.sma200 !== null) direction = ind.close >= ind.sma200 ? "PUT" : "CALL";
  if (!direction) direction = "PUT";
  const trade = pick ? buildSpread(chain.options, pick.expiry, direction) : null;
  const { checks, light } = grade(stretch, trade, chain.iv30_pct, ind ? ind.rv20 : null);
  return {
    symbol,
    timestamp: chain.timestamp,
    today,
    price: chain.price,
    change_pct: chain.change_pct,
    iv30_pct: chain.iv30_pct,
    last_day: bars.length ? { date: bars[bars.length - 1].date, ...ind } : null,
    stretch,
    direction,
    dte: pick ? pick.dte : null,
    trade,
    checks,
    light,
  };
}

async function getJson(url, timeoutMs) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, {
      signal: controller.signal,
      headers: { "user-agent": "premium-finder/1.0 (research)", accept: "application/json" },
      redirect: "follow",
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } finally {
    clearTimeout(timer);
  }
}

export async function fetchAndAnalyze(symbol, now = new Date()) {
  if (!SYMBOLS.includes(symbol)) throw new Error("unsupported symbol");
  const [historyPayload, chainPayload] = await Promise.all([
    getJson(HISTORY_URL(symbol), 15000),
    getJson(CHAIN_URL(symbol), 20000),
  ]);
  return analyze({ symbol, historyPayload, chainPayload, now });
}
