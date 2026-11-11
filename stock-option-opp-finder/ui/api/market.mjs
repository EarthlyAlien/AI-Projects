import { SYMBOLS, fetchAndAnalyze } from "../core/market.mjs";

const CACHE_MS = 2 * 60 * 1000;
const cache = new Map();

export async function GET(request) {
  const symbol = (new URL(request.url).searchParams.get("symbol") || "").toUpperCase();
  if (!SYMBOLS.includes(symbol)) {
    return Response.json({ error: "symbol must be SPY or NBIS" }, { status: 400 });
  }
  const hit = cache.get(symbol);
  if (hit && Date.now() - hit.at < CACHE_MS) {
    return Response.json(hit.body, { headers: { "cache-control": "public, max-age=60, s-maxage=120" } });
  }
  try {
    const body = { source: "live", ...(await fetchAndAnalyze(symbol)) };
    cache.set(symbol, { at: Date.now(), body });
    return Response.json(body, { headers: { "cache-control": "public, max-age=60, s-maxage=120" } });
  } catch (error) {
    return Response.json(
      { error: "live data unavailable", reason: error instanceof Error ? error.name : "error" },
      { status: 502, headers: { "cache-control": "no-store" } }
    );
  }
}
