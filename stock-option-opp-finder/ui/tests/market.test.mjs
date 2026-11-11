import assert from "node:assert/strict";
import { test } from "node:test";

import { analyze, buildSpread, finishedBars, grade, parseOcc, pickExpiry } from "../core/market.mjs";

const put = (strike, bid, ask, delta, expiration = "2026-11-25") => ({ expiration, type: "PUT", strike, bid, ask, iv: 0.2, delta });

test("parseOcc reads expiry, side and strike", () => {
  assert.deepEqual(parseOcc("B1SPY261113C00710000"), { expiration: "2026-11-13", type: "CALL", strike: 710 });
  assert.equal(parseOcc("junk"), null);
});

test("pickExpiry prefers about two weeks, never today or tomorrow", () => {
  const pick = pickExpiry(["2026-11-11", "2026-11-12", "2026-11-20", "2026-11-25", "2026-12-18"], "2026-11-11");
  assert.equal(pick.expiry, "2026-11-25");
  assert.equal(pick.dte, 14);
  assert.equal(pickExpiry(["2026-11-12"], "2026-11-11"), null);
});

test("buildSpread sells near 0.30 delta and buys protection about 5 points away", () => {
  const legs = [put(760, 9, 9.1, -0.45), put(755, 6, 6.1, -0.31), put(754, 5.6, 5.7, -0.29), put(750, 4.4, 4.5, -0.22), put(745, 3, 3.1, -0.15)];
  const trade = buildSpread(legs, "2026-11-25", "PUT");
  assert.equal(trade.short_strike, 755);
  assert.equal(trade.long_strike, 750);
  assert.equal(trade.credit, 1.5);
  assert.equal(trade.max_profit, 150);
  assert.equal(trade.max_loss, 350);
  assert.equal(trade.breakeven, 753.5);
  assert.equal(trade.take_profit_debit, 0.75);
});

test("finishedBars drops today's bar while the market is open", () => {
  const bars = [{ date: "2026-11-10", close: 1 }, { date: "2026-11-11", close: 2 }];
  assert.equal(finishedBars(bars, new Date("2026-11-11T16:30:00Z")).length, 1);
  assert.equal(finishedBars(bars, new Date("2026-11-11T22:00:00Z")).length, 2);
});

test("grade is red without a stretch and green only when every check passes", () => {
  const trade = { short_delta: -0.3, max_loss: 350 };
  assert.equal(grade(0, trade, 25, 0.15).light, "red");
  assert.equal(grade(1, trade, 25, 0.15).light, "green");
  assert.equal(grade(1, trade, 10, 0.15).light, "yellow");
});

test("analyze builds a full answer from raw payloads", () => {
  const history = { data: Array.from({ length: 220 }, (_, i) => ({ date: `2026-${String(1 + Math.floor(i / 28)).padStart(2, "0")}-${String(1 + (i % 28)).padStart(2, "0")}`, close: 100 + i * 0.1 })) };
  const chain = {
    timestamp: "2026-11-11 16:00:00",
    data: {
      current_price: 122,
      price_change_percent: 0.5,
      iv30: 20,
      options: [
        { option: "SPY261125P00120000", bid: 2, ask: 2.1, iv: 0.2, delta: -0.3 },
        { option: "SPY261125P00115000", bid: 0.7, ask: 0.8, iv: 0.2, delta: -0.15 },
      ],
    },
  };
  const result = analyze({ symbol: "SPY", historyPayload: history, chainPayload: chain, now: new Date("2026-11-11T16:30:00Z") });
  assert.equal(result.trade.short_strike, 120);
  assert.equal(result.trade.long_strike, 115);
  assert.equal(result.light, "red");
  assert.equal(result.checks[0].id, "stretch");
});
