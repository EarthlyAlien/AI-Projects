// Writes ui/live.json: the same live check the server route returns, saved so the
// page still has something truthful to show when live data cannot be reached.
// Run from stock-option-opp-finder: node ui/core/save-check.mjs

import { writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { SYMBOLS, fetchAndAnalyze } from "./market.mjs";

const out = { saved_at: new Date().toISOString(), symbols: {} };
for (const symbol of SYMBOLS) {
  try {
    out.symbols[symbol] = { source: "saved", ...(await fetchAndAnalyze(symbol)) };
    console.log(`${symbol}: ${out.symbols[symbol].light}`);
  } catch (error) {
    out.symbols[symbol] = { error: String(error && error.message ? error.message : error) };
    console.log(`${symbol}: failed (${out.symbols[symbol].error})`);
  }
}
const target = fileURLToPath(new URL("../live.json", import.meta.url));
writeFileSync(target, JSON.stringify(out, null, 1));
console.log(`wrote ${target}`);
