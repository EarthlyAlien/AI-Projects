"use strict";

const FAMILY_LABEL = {
  mr_fade: "After a stretch",
  high_iv: "When options are expensive",
  trend_aligned: "With the trend",
};

const CBOE_CHAIN = (symbol) => "https://cdn.cboe.com/api/global/delayed_quotes/options/" + symbol + ".json";

let DATA = null;

function pct(value, digits) {
  if (value === null || value === undefined || Number.isNaN(value)) return "n/a";
  return (value * 100).toFixed(digits === undefined ? 1 : digits) + "%";
}

function num(value, digits) {
  if (value === null || value === undefined || Number.isNaN(value)) return "n/a";
  return Number(value).toFixed(digits === undefined ? 2 : digits);
}

function money(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "n/a";
  return "$" + Number(value).toLocaleString("en-US", { maximumFractionDigits: 0 });
}

function esc(text) {
  return String(text).replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[ch]));
}

function lineChart(series, width, height, color) {
  if (!series.length) return "<p class='hint'>No price data.</p>";
  const closes = series.map((row) => row.close);
  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const pad = (max - min) * 0.05 || 1;
  const x = (i) => (i / (series.length - 1)) * (width - 8) + 4;
  const y = (v) => height - 8 - ((v - (min - pad)) / (max - min + 2 * pad)) * (height - 16);
  const points = series.map((row, i) => x(i).toFixed(1) + "," + y(row.close).toFixed(1)).join(" ");
  return (
    '<svg viewBox="0 0 ' + width + " " + height + '" role="img" aria-label="price chart">' +
    '<line x1="4" y1="' + y(min) + '" x2="' + (width - 4) + '" y2="' + y(min) + '" stroke="#d5dbdb"/>' +
    '<polyline fill="none" stroke="' + color + '" stroke-width="1.6" points="' + points + '"/>' +
    '<text x="6" y="14" font-size="11" fill="#5d6d7e">high ' + num(max) + "</text>" +
    '<text x="6" y="' + (height - 10) + '" font-size="11" fill="#5d6d7e">low ' + num(min) + " · " +
    esc(series[0].date) + " to " + esc(series[series.length - 1].date) + "</text></svg>"
  );
}

function histogram(values, width, height) {
  if (!values.length) return "<p class='hint'>No windows.</p>";
  const lo = Math.min(...values, -0.02);
  const hi = Math.max(...values, 0.02);
  const bins = new Array(14).fill(0);
  values.forEach((v) => {
    const idx = Math.min(bins.length - 1, Math.max(0, Math.floor(((v - lo) / (hi - lo)) * bins.length)));
    bins[idx] += 1;
  });
  const top = Math.max(...bins) || 1;
  const bw = width / bins.length;
  let rects = "";
  bins.forEach((count, i) => {
    const mid = lo + ((i + 0.5) / bins.length) * (hi - lo);
    const h = (count / top) * (height - 22);
    rects += '<rect x="' + (i * bw + 1).toFixed(1) + '" y="' + (height - 18 - h).toFixed(1) +
      '" width="' + (bw - 2).toFixed(1) + '" height="' + h.toFixed(1) + '" fill="' +
      (mid >= 0 ? "#1e8449" : "#b03a2e") + '" opacity="0.75"><title>' + count + " windows near " +
      pct(mid) + "</title></rect>";
  });
  const zeroX = ((0 - lo) / (hi - lo)) * width;
  return '<svg viewBox="0 0 ' + width + " " + height + '" role="img" aria-label="histogram">' + rects +
    '<line x1="' + zeroX.toFixed(1) + '" y1="2" x2="' + zeroX.toFixed(1) + '" y2="' + (height - 18) +
    '" stroke="#17202a" stroke-dasharray="3 3"/>' +
    '<text x="4" y="' + (height - 4) + '" font-size="11" fill="#5d6d7e">' + pct(lo) + "</text>" +
    '<text x="' + (width - 52) + '" y="' + (height - 4) + '" font-size="11" fill="#5d6d7e">' + pct(hi) + "</text></svg>";
}

function payoffAt(type, spot, shortStrike, longStrike, credit) {
  if (type === "put") {
    return credit - Math.max(0, shortStrike - spot) + Math.max(0, longStrike - spot);
  }
  return credit - Math.max(0, spot - shortStrike) + Math.max(0, spot - longStrike);
}

function payoffChart(type, shortStrike, longStrike, credit, contracts) {
  const widthStrike = Math.abs(shortStrike - longStrike);
  const center = (shortStrike + longStrike) / 2;
  const lo = center - widthStrike * 4;
  const hi = center + widthStrike * 4;
  const W = 720;
  const H = 190;
  const maxProfit = credit * 100 * contracts;
  const maxLoss = (widthStrike - credit) * 100 * contracts;
  const yMax = Math.max(maxProfit, maxLoss) * 1.15 || 1;
  const x = (s) => ((s - lo) / (hi - lo)) * (W - 16) + 8;
  const y = (p) => H / 2 - (p / yMax) * (H / 2 - 14);
  let points = "";
  for (let i = 0; i <= 80; i += 1) {
    const spot = lo + ((hi - lo) * i) / 80;
    points += x(spot).toFixed(1) + "," + y(payoffAt(type, spot, shortStrike, longStrike, credit) * 100 * contracts).toFixed(1) + " ";
  }
  return '<svg viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="payoff chart">' +
    '<line x1="8" y1="' + y(0) + '" x2="' + (W - 8) + '" y2="' + y(0) + '" stroke="#d5dbdb"/>' +
    '<line x1="' + x(shortStrike) + '" y1="8" x2="' + x(shortStrike) + '" y2="' + (H - 8) + '" stroke="#9a7d0a" stroke-dasharray="3 3"/>' +
    '<line x1="' + x(longStrike) + '" y1="8" x2="' + x(longStrike) + '" y2="' + (H - 8) + '" stroke="#b03a2e" stroke-dasharray="3 3"/>' +
    '<polyline fill="none" stroke="#2456a6" stroke-width="2" points="' + points + '"/>' +
    '<text x="10" y="16" font-size="11" fill="#1e8449">max profit ' + money(maxProfit) + "</text>" +
    '<text x="10" y="' + (H - 8) + '" font-size="11" fill="#b03a2e">max loss ' + money(maxLoss) + "</text>" +
    '<text x="' + Math.min(W - 120, x(shortStrike) + 4) + '" y="16" font-size="11" fill="#9a7d0a">short ' + num(shortStrike, 0) + "</text></svg>";
}

function renderVerdicts() {
  const host = document.getElementById("verdicts");
  const rows = (DATA.ranked_candidates || []).slice(0, 4);
  host.innerHTML = rows.map((row, index) => {
    const small = row.n < 30;
    const weak = (row.mean_signed_return || 0) <= 0;
    const pill = small
      ? '<span class="pill small">n=' + row.n + " · descriptive</span>"
      : (weak ? '<span class="pill weak">n=' + row.n + " · weak drift</span>" : '<span class="pill ok">n=' + row.n + "</span>");
    return '<div class="verdict"><h3>' + (index + 1) + ". " + esc(row.symbol) + " " +
      esc(FAMILY_LABEL[row.family] || row.family) + ", " + row.horizon + " session" + (row.horizon > 1 ? "s" : "") + "</h3>" +
      pill +
      "<p>Signed drift <b>" + pct(row.mean_signed_return) + "</b> · win rate " + pct(row.win_rate) + "</p>" +
      "<p>Moved too far by the close: " + pct(row.breach_close_rate) +
      "<br>Moved too far during the day: " + pct(row.breach_intra_rate) + "</p></div>";
  }).join("");
  const direct = DATA.direct_summary || {};
  document.getElementById("directNote").textContent =
    "When we tried to check real SPY option prices 1-2 days later, we could only do it " + (direct.marked || 0) +
    " times out of " + ((direct.marked || 0) + (direct.unmarked || 0)) + " tries. The other times the free data had no price, and we refused to guess. That is why these cards grade the stock's behaviour instead, and say so.";
}

function renderPrices(symbol) {
  document.querySelectorAll("[data-symbol]").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.symbol === symbol);
  });
  const series = (DATA.prices || {})[symbol] || [];
  document.getElementById("priceChart").innerHTML = lineChart(series, 720, 200, symbol === "SPY" ? "#2456a6" : "#7d3c98");
  const path = (DATA.pair_paths || []).find((row) => row.symbol === symbol) || {};
  document.getElementById("pathStats").textContent =
    symbol + " study return " + pct(path.simple_return) + " · max drawdown " + pct(path.max_drawdown) +
    " · realized vol " + pct(path.realized_vol) + " · sessions " + (path.sessions || series.length);
}

function explorerRows() {
  const symbol = document.getElementById("exSymbol").value;
  const family = document.getElementById("exFamily").value;
  const horizon = Number(document.getElementById("exHorizon").value);
  return (DATA.windows || []).filter(
    (row) => row.symbol === symbol && row.family === family && row.horizon === horizon
  );
}

function renderExplorer() {
  const rows = explorerRows();
  const symbol = document.getElementById("exSymbol").value;
  const family = document.getElementById("exFamily").value;
  const horizon = Number(document.getElementById("exHorizon").value);
  const summary = (DATA.window_summaries || []).find(
    (row) => row.symbol === symbol && row.family === family && row.horizon === horizon
  ) || {};
  const stat = (label, value, cls) =>
    '<div class="stat"><b class="' + (cls || "") + '">' + value + "</b><span>" + label + "</span></div>";
  document.getElementById("exStats").innerHTML =
    stat("windows", String(summary.n || rows.length)) +
    stat("mean signed drift", pct(summary.mean_signed_return), (summary.mean_signed_return || 0) >= 0 ? "pos" : "neg") +
    stat("win rate", pct(summary.win_rate)) +
    stat("adverse close breach", pct(summary.breach_close_rate)) +
    stat("adverse intraday breach", pct(summary.breach_intra_rate)) +
    stat("IV minus forward RV (SPY)", summary.mean_iv_minus_forward_rv === null || summary.mean_iv_minus_forward_rv === undefined ? "n/a" : num(summary.mean_iv_minus_forward_rv, 4));
  document.getElementById("exHist").innerHTML = histogram(rows.map((row) => row.signed_return), 720, 150);
  const shown = rows.slice().sort((a, b) => (a.signal_date < b.signal_date ? 1 : -1)).slice(0, 12);
  document.getElementById("exTable").innerHTML =
    "<table><tr><th>Signal</th><th>Side</th><th>Signed</th><th>Adverse close</th><th>Breach?</th></tr>" +
    shown.map((row) => "<tr><td>" + esc(row.signal_date) + "</td><td>" + (row.side === 1 ? "bullish credit" : "bearish credit") +
      "</td><td>" + pct(row.signed_return) + "</td><td>" + pct(row.adverse_close) + "</td><td>" +
      (row.breach_intra ? "intraday" : (row.breach_close ? "close" : "no")) + "</td></tr>").join("") + "</table>" +
    (rows.length > shown.length ? '<p class="hint">Showing the latest ' + shown.length + " of " + rows.length + " windows.</p>" : "");
}

function renderPayoff() {
  const type = document.getElementById("pfType").value;
  const shortStrike = Number(document.getElementById("pfShort").value || 0);
  const longStrike = Number(document.getElementById("pfLong").value || 0);
  const credit = Number(document.getElementById("pfCredit").value || 0);
  const contracts = Math.max(1, Number(document.getElementById("pfContracts").value || 1));
  const widthStrike = Math.abs(shortStrike - longStrike);
  const maxProfit = credit * 100 * contracts;
  const maxLoss = Math.max(0, (widthStrike - credit) * 100 * contracts);
  const breakeven = type === "put" ? shortStrike - credit : shortStrike + credit;
  const stat = (label, value) => '<div class="stat"><b>' + value + "</b><span>" + label + "</span></div>";
  document.getElementById("pfStats").innerHTML =
    stat("credit kept if closed flat", money(maxProfit)) +
    stat("max loss (defined risk)", money(maxLoss)) +
    stat("breakeven at expiry", num(breakeven)) +
    stat("close-at-half-credit target", money(maxProfit / 2) + " profit") +
    stat("width", num(widthStrike, 1) + " pts");
  document.getElementById("pfChart").innerHTML =
    widthStrike > 0 && credit > 0
      ? payoffChart(type, shortStrike, longStrike, credit, contracts)
      : '<p class="hint">Enter a positive width and credit.</p>';
}

function renderVariants() {
  const family = document.getElementById("varFamily").value;
  const rows = (DATA.variants || []).filter((row) => family === "all" || row.family === family);
  document.getElementById("varTable").innerHTML =
    "<table><tr><th>Variant</th><th>Marked</th><th>Unmarked</th><th>Marked share</th><th>Expectancy (marked only)</th><th>Evidence</th></tr>" +
    rows.map((row) => {
      const total = (row.n || 0) + (row.unmarked_n || 0);
      const share = total ? row.n / total : 0;
      return "<tr><td>" + esc(row.variant) + "</td><td>" + row.n + "</td><td>" + row.unmarked_n +
        '</td><td><div class="bar"><i style="width:' + (share * 100).toFixed(1) + '%"></i></div></td><td>' +
        (row.n ? money(row.expectancy) : "n/a") + "</td><td>" + esc(row.evidence || "") + "</td></tr>";
    }).join("") + "</table>" +
    '<p class="hint">Green is the share of entries whose exit strikes were still quoted. The rest were left unmarked rather than priced with a model.</p>';
}

function preset(symbol) {
  const item = (DATA.illustrations || []).find((row) => row.symbol === symbol);
  if (!item) return;
  document.getElementById("pfType").value = "put";
  document.getElementById("pfShort").value = item.short_strike;
  document.getElementById("pfLong").value = item.long_strike;
  document.getElementById("pfCredit").value = Number(item.credit).toFixed(2);
  renderPayoff();
}

function parseOcc(code) {
  const match = /(\d{6})([CP])(\d{8})$/.exec(code || "");
  if (!match) return null;
  const expiry = "20" + match[1].slice(0, 2) + "-" + match[1].slice(2, 4) + "-" + match[1].slice(4, 6);
  return { expiration: expiry, type: match[2] === "C" ? "CALL" : "PUT", strike: Number(match[3]) / 1000 };
}

function buildCandidate(options, expiration, right) {
  const legs = options.filter((row) =>
    row.expiration === expiration && row.type === right &&
    row.bid > 0 && row.ask >= row.bid && row.delta !== null && row.delta !== undefined);
  if (!legs.length) return null;
  const target = right === "PUT" ? -0.30 : 0.30;
  const short = legs.reduce((best, row) =>
    Math.abs(row.delta - target) < Math.abs(best.delta - target) ? row : best, legs[0]);
  const strikes = [...new Set(legs.map((row) => row.strike))].sort((a, b) => a - b);
  const beyond = right === "PUT"
    ? strikes.filter((s) => s < short.strike)
    : strikes.filter((s) => s > short.strike);
  const wingTarget = right === "PUT" ? short.strike - 5 : short.strike + 5;
  const wingStrike = beyond.reduce((best, s) =>
    Math.abs(s - wingTarget) < Math.abs(best - wingTarget) ? s : best, beyond[0]);
  if (wingStrike === undefined) return null;
  const wing = legs.find((row) => row.strike === wingStrike);
  const credit = short.bid - wing.ask;
  const width = Math.abs(short.strike - wingStrike);
  if (credit <= 0 || width <= 0) return null;
  return {
    right, expiration,
    short_strike: short.strike, long_strike: wingStrike,
    short_bid: short.bid, long_ask: wing.ask, short_delta: short.delta, short_iv: short.iv,
    credit, width,
    max_loss_dollars: (width - credit) * 100,
    max_profit_dollars: credit * 100,
    breakeven: right === "PUT" ? short.strike - credit : short.strike + credit,
  };
}

function liveChecks(context, candidate, iv30Percent, spot) {
  const checks = [];
  if (!context || !candidate) return checks;
  if (iv30Percent !== null && iv30Percent !== undefined && context.rv20) {
    checks.push({
      label: "Are the options expensive?",
      pass: iv30Percent / 100 > context.rv20,
      detail: "The option market charges about " + num(iv30Percent, 0) + "% for expected movement. This stock actually moved at about " +
        num(context.rv20 * 100, 0) + "% a year pace in the last 20 days. Selling only makes sense when the charge is higher.",
    });
  }
  const want = candidate.right === "PUT" ? 1 : -1;
  const stretched = (context.signals || {}).mr_fade === want;
  checks.push({
    label: "Did the stock just get stretched? (our best-tested pattern)",
    pass: stretched,
    detail: stretched
      ? "The last finished trading day did show that stretch."
      : "The last finished trading day did not show that stretch, so this is not our tested pattern.",
  });
  if (spot && context.sma50) {
    const withTrend = candidate.right === "PUT" ? spot > context.sma50 : spot < context.sma50;
    checks.push({
      label: "Is the trade on the calm side of the trend?",
      pass: withTrend,
      detail: "Price now " + num(spot) + ", 50-day average " + num(context.sma50) + ". A put spread wants price above that average; a call spread wants it below.",
    });
  }
  checks.push({
    label: "Is the worst case small and known?",
    pass: candidate.max_loss_dollars <= 1000,
    detail: "Worst case on 1 contract is $" + num(candidate.max_loss_dollars, 0) + ". You collect $" +
      num(candidate.max_profit_dollars, 0) + " if you close flat. Never sell without the protective second leg.",
  });
  checks.push({
    label: "Is the strike a reasonable distance away?",
    pass: Math.abs(candidate.short_delta) <= 0.35,
    detail: "The sold option's delta is " + num(candidate.short_delta) + ". Traders read 0.30 as roughly a 30% chance of ending in the money. Much closer is gambling, not premium collecting.",
  });
  return checks;
}

function verdictText(checks) {
  if (!checks.length) return "We could not run the checks.";
  const passed = checks.filter((check) => check.pass).length;
  if (passed === checks.length) return "This matches our tested pattern.";
  if (passed >= checks.length - 1) return "This partly matches. Read the failed check first.";
  return "This does not match our tested pattern.";
}

function renderLiveResult(symbol, right, spot, iv30Percent, timestamp, candidate, checks, sourceNote, nearRows) {
  const host = document.getElementById("liveOut");
  const checksHtml = checks.map((check) =>
    '<div class="verdict"><p><span class="pill ' + (check.pass ? "ok" : "weak") + '">' +
    (check.pass ? "YES" : "NO") + "</span> <b>" + esc(check.label) + "</b></p><p>" + esc(check.detail) + "</p></div>"
  ).join("");
  let html = '<p class="hint">' + esc(sourceNote) + " Prices as of " + esc(timestamp || "n/a") + ".</p>";
  html += '<div class="stats">' +
    '<div class="stat"><b>' + num(spot) + "</b><span>" + esc(symbol) + " price now</span></div>" +
    '<div class="stat"><b>' + (iv30Percent === null || iv30Percent === undefined ? "n/a" : num(iv30Percent, 1) + "%") + "</b><span>option expensiveness (IV30)</span></div>" +
    '<div class="stat"><b>' + (candidate ? money(candidate.max_profit_dollars) : "n/a") + "</b><span>money collected, 1 contract</span></div>" +
    '<div class="stat"><b>' + (candidate ? money(candidate.max_loss_dollars) : "n/a") + "</b><span>worst case, 1 contract</span></div></div>";
  if (candidate) {
    html += '<p><b>' + esc(verdictText(checks)) + "</b> The trade we built: sell the " + num(candidate.short_strike, 0) + " " +
      candidate.right.toLowerCase() + " at " + num(candidate.short_bid) + ", buy the " + num(candidate.long_strike, 0) +
      " at " + num(candidate.long_ask) + ", both expiring " + esc(candidate.expiration) + ". You collect $" +
      num(candidate.max_profit_dollars, 0) + ". If the stock ends past " + num(candidate.breakeven) +
      " the wrong way, losses grow to the worst case above. Plan: close in 1-2 days, or when half the money is safe.</p>";
  } else {
    html += "<p>No safe two-leg trade could be built from this chain.</p>";
  }
  html += '<div class="grid">' + checksHtml + "</div>";
  if (nearRows && nearRows.length) {
    html += "<h3>Options near today's price (" + esc(candidate ? candidate.expiration : "") + ")</h3><table><tr><th>Strike</th><th>You sell at</th><th>You buy at</th><th>Expensiveness (IV)</th><th>Delta</th></tr>" +
      nearRows.map((row) => "<tr><td>" + num(row.strike, 0) + "</td><td>" + num(row.bid) + "</td><td>" + num(row.ask) +
        "</td><td>" + pct(row.iv) + "</td><td>" + num(row.delta, 3) + "</td></tr>").join("") + "</table>";
  }
  host.innerHTML = html;
}

async function checkLive() {
  const symbol = document.getElementById("liveSymbol").value;
  const right = document.getElementById("liveIdea").value;
  const host = document.getElementById("liveOut");
  host.innerHTML = '<p class="hint">Fetching today\'s chain for ' + esc(symbol) + "…</p>";
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 20000);
    const response = await fetch(CBOE_CHAIN(symbol), { signal: controller.signal, cache: "no-store" });
    clearTimeout(timer);
    if (!response.ok) throw new Error("HTTP " + response.status);
    const payload = await response.json();
    const data = payload.data || {};
    const options = [];
    (data.options || []).forEach((item) => {
      const parsed = parseOcc(item.option);
      if (parsed) options.push({ ...parsed, bid: item.bid, ask: item.ask, iv: item.iv, delta: item.delta });
    });
    const today = String(payload.timestamp || "").slice(0, 10);
    const expirations = [...new Set(options.map((row) => row.expiration))].sort();
    const expiry = expirations.find((day) => day > today) || expirations[expirations.length - 1];
    const candidate = buildCandidate(options, expiry, right);
    const context = (DATA.symbol_context || {})[symbol] || {};
    const checks = liveChecks(context, candidate, data.iv30, data.current_price);
    const spot = data.current_price;
    const nearRows = options
      .filter((row) => row.expiration === expiry && row.type === right && spot && Math.abs(row.strike - spot) / spot <= 0.1)
      .sort((a, b) => Math.abs(a.strike - spot) - Math.abs(b.strike - spot))
      .slice(0, 10)
      .sort((a, b) => a.strike - b.strike);
    renderLiveResult(symbol, right, spot, data.iv30, payload.timestamp, candidate, checks,
      "Live from CBOE delayed quotes (about 15 minutes delayed). This is a check, not a trade instruction.", nearRows);
  } catch (error) {
    try {
      const saved = await (await fetch("live.json")).json();
      const entry = (saved.symbols || {})[symbol];
      if (!entry || entry.error) throw new Error(entry ? entry.error : "no saved check");
      const candidate = (entry.candidates || {})[right];
      renderLiveResult(symbol, right, entry.current_price, entry.iv30_percent, entry.timestamp,
        candidate, candidate ? candidate.checks || [] : [],
        "The live fetch was blocked (" + error.message + "), so this is the last saved check. It is not live.",
        (entry.near_options || []).filter((row) => row.type === right)
          .sort((a, b) => Math.abs(a.strike - entry.current_price) - Math.abs(b.strike - entry.current_price))
          .slice(0, 10)
          .sort((a, b) => a.strike - b.strike));
    } catch (fallbackError) {
      host.innerHTML = '<p class="hint">We could not fetch the live chain (' + esc(error.message) +
        ") and no saved check loaded (" + esc(fallbackError.message) + "). Nothing was guessed.</p>";
    }
  }
}

async function boot() {
  const response = await fetch("data.json");
  DATA = await response.json();
  document.getElementById("asOf").textContent =
    "last completed session " + (DATA.last_complete || "n/a") + " · static checked-in data";
  renderVerdicts();
  renderPrices("SPY");
  renderExplorer();
  renderPayoff();
  renderVariants();
  document.querySelectorAll("[data-symbol]").forEach((btn) => {
    btn.addEventListener("click", () => renderPrices(btn.dataset.symbol));
  });
  ["exSymbol", "exFamily", "exHorizon"].forEach((id) => {
    document.getElementById(id).addEventListener("change", renderExplorer);
  });
  ["pfType", "pfShort", "pfLong", "pfCredit", "pfContracts"].forEach((id) => {
    document.getElementById(id).addEventListener("input", renderPayoff);
    document.getElementById(id).addEventListener("change", renderPayoff);
  });
  document.getElementById("presetSpy").addEventListener("click", () => preset("SPY"));
  document.getElementById("presetNbis").addEventListener("click", () => preset("NBIS"));
  document.getElementById("varFamily").addEventListener("change", renderVariants);
  document.getElementById("liveBtn").addEventListener("click", checkLive);
  document.getElementById("liveSymbol").addEventListener("change", checkLive);
  document.getElementById("liveIdea").addEventListener("change", checkLive);
  checkLive();
}

boot().catch((error) => {
  document.getElementById("asOf").textContent = "failed to load data.json: " + error.message;
});
