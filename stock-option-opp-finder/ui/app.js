"use strict";

const FAMILY_LABEL = {
  mr_fade: "Mean-reversion fade",
  high_iv: "High-IV selling",
  trend_aligned: "Trend-aligned",
};

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
      "<p>Adverse close beyond expected move: " + pct(row.breach_close_rate) +
      "<br>Adverse intraday: " + pct(row.breach_intra_rate) + "</p></div>";
  }).join("");
  const direct = DATA.direct_summary || {};
  document.getElementById("directNote").textContent =
    "Direct SPY option marks at 1-2 sessions: " + (direct.marked || 0) + " marked closes across 18 variants, " +
    (direct.unmarked || 0) + " unmarked. That is why the cards use the underlying proxy and say so.";
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
}

boot().catch((error) => {
  document.getElementById("asOf").textContent = "failed to load data.json: " + error.message;
});
