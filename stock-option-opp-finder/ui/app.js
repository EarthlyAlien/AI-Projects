"use strict";

const SYMBOLS = ["SPY", "NBIS"];
const NAMES = { SPY: "SPY — the whole US stock market", NBIS: "NBIS — Nebius, one fast-moving stock" };
const FAMILY_LABEL = { mr_fade: "After a big, fast move", high_iv: "When options are pricey", trend_aligned: "With the trend" };
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

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

function strike(value) {
  return Number.isInteger(value) ? String(value) : Number(value).toFixed(1);
}

function esc(text) {
  return String(text).replace(/[&<>"']/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
}

function isoDate(iso) {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d));
}

function shortDate(iso) {
  const day = isoDate(iso);
  return MONTHS[day.getUTCMonth()] + " " + day.getUTCDate();
}

function closeByDate(todayIso, tradingDays) {
  const day = isoDate(todayIso);
  let left = tradingDays;
  while (left > 0) {
    day.setUTCDate(day.getUTCDate() + 1);
    const weekday = day.getUTCDay();
    if (weekday !== 0 && weekday !== 6) left -= 1;
  }
  return WEEKDAYS[day.getUTCDay()] + ", " + MONTHS[day.getUTCMonth()] + " " + day.getUTCDate();
}

function patternHistory(symbol) {
  return (DATA.window_summaries || []).find((row) => row.symbol === symbol && row.family === "mr_fade" && row.horizon === 2);
}

// ---------- The 30-second answer ----------

function headline(result) {
  if (result.light === "green") return { word: "TRADE IT — practice first", why: "The pattern we tested is here today, and every safety check passed." };
  if (result.light === "yellow") {
    const failed = result.checks.find((check) => !check.pass);
    return { word: "ALMOST — WAIT", why: "The pattern is here, but one check failed: " + (failed ? failed.label.toLowerCase() : "see why") + "" };
  }
  const stretch = result.checks.find((check) => check.id === "stretch");
  if (stretch && !stretch.pass) {
    return { word: "SKIP TODAY", why: "The last finished day was a normal day. This only works right after a big, fast move. Check again after the next close." };
  }
  return { word: "SKIP TODAY", why: "We could not build a safe spread from today's prices." };
}

function ticketHtml(result, open) {
  const trade = result.trade;
  if (!trade) return '<p class="hint">No safe two-option spread could be built from today\'s prices.</p>';
  const kind = trade.right === "PUT" ? "Put" : "Call";
  const loseIf = trade.right === "PUT"
    ? "You start losing only if " + esc(result.symbol) + " ends below " + num(trade.breakeven)
    : "You start losing only if " + esc(result.symbol) + " ends above " + num(trade.breakeven);
  const exp = shortDate(trade.expiry);
  const body =
    '<div class="ticket"><h3>' + (open ? "Your order" : "The order (not for today)") + "</h3><ol>" +
    "<li>In your broker, pick a <b>spread</b> order (2 options sent together). Never sell the first option alone.</li>" +
    '<li><span class="sell">SELL</span> to open: <span class="leg">1 × ' + esc(result.symbol) + " " + exp + " $" + strike(trade.short_strike) + " " + kind + "</span></li>" +
    '<li><span class="buy">BUY</span> to open: <span class="leg">1 × ' + esc(result.symbol) + " " + exp + " $" + strike(trade.long_strike) + " " + kind + "</span></li>" +
    "<li>Limit price: <b>$" + num(trade.credit) + " credit</b> or more.</li></ol>" +
    '<div class="money"><div class="in"><b>+' + money(trade.max_profit) + '</b><span>you get paid now</span></div>' +
    '<div class="worst"><b>−' + money(trade.max_loss) + '</b><span>worst case</span></div>' +
    '<div class="line"><b>$' + num(trade.breakeven) + "</b><span>" + (trade.right === "PUT" ? "safe above this" : "safe below this") + "</span></div></div>" +
    '<p class="exit"><b>Get out:</b> close by <b>' + closeByDate(result.today, 2) + "</b>, or sooner as soon as you can buy the spread back for <b>$" +
    num(trade.take_profit_debit) + "</b> (half the money is then yours).</p>" +
    '<p class="warn">' + loseIf + ". Practice this in your broker's paper-trading mode before using real money.</p></div>";
  if (open) return body;
  return "<details><summary>Show the order anyway</summary>" + body + "</details>";
}

function checksHtml(result) {
  return "<details><summary>Why?</summary><ul class=\"checks\">" +
    result.checks.map((check) =>
      '<li><span class="tag ' + (check.pass ? "yes" : "no") + '">' + (check.pass ? "YES" : "NO") + "</span><b>" +
      esc(check.label) + "</b><br>" + esc(check.detail) + "</li>").join("") + "</ul></details>";
}

function sourceLine(result, savedAt) {
  if (result.source === "live") {
    return "Live prices from CBOE, about 15 minutes delayed (" + esc(result.timestamp || "") + " UTC). Pattern uses the last finished day, " + esc(result.last_day ? result.last_day.date : "n/a") + ".";
  }
  return "Live prices could not load here, so this is the saved check from " + esc(savedAt || result.timestamp || "an earlier run") + ". Do not trade from a saved check.";
}

function renderAnswer(symbol, result, savedAt) {
  const card = document.getElementById("card-" + symbol);
  if (!result || result.error) {
    card.className = "answer";
    card.innerHTML = '<p class="name">' + esc(NAMES[symbol]) + "</p><p>We could not load prices right now, so there is no answer. Nothing was guessed.</p>";
    return;
  }
  const head = headline(result);
  const change = result.change_pct === null || result.change_pct === undefined ? "" : " (" + (result.change_pct >= 0 ? "+" : "") + num(result.change_pct, 1) + "% today)";
  const history = patternHistory(symbol);
  const historyLine = history && history.n
    ? "Last year this pattern showed up on " + history.n + " days for " + symbol + "; the stock moved the seller's way " +
      Math.round(history.win_rate * history.n) + " of those " + history.n + " times."
    : "";
  card.className = "answer " + result.light;
  card.innerHTML =
    '<p class="name">' + esc(NAMES[symbol]) + "</p>" +
    '<p class="price">Price now $' + num(result.price) + esc(change) + "</p>" +
    '<div class="light"><span class="big ' + result.light + '"></span><h2>' + esc(head.word) + "</h2></div>" +
    '<p class="why">' + esc(head.why) + "</p>" +
    ticketHtml(result, result.light === "green" || result.light === "yellow") +
    checksHtml(result) +
    (historyLine ? '<p class="source">' + esc(historyLine) + "</p>" : "") +
    '<p class="source">' + sourceLine(result, savedAt) + "</p>";
}

async function loadAnswers() {
  let saved = null;
  for (const symbol of SYMBOLS) {
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 25000);
      const response = await fetch("api/market?symbol=" + symbol, { signal: controller.signal, cache: "no-store" });
      clearTimeout(timer);
      if (!response.ok) throw new Error("HTTP " + response.status);
      const result = await response.json();
      if (result.error) throw new Error(result.error);
      renderAnswer(symbol, result);
    } catch (error) {
      try {
        if (!saved) saved = await (await fetch("live.json", { cache: "no-store" })).json();
        renderAnswer(symbol, (saved.symbols || {})[symbol], saved.saved_at);
      } catch (fallbackError) {
        renderAnswer(symbol, null);
      }
    }
  }
}

function renderProof() {
  const spy = patternHistory("SPY") || {};
  const nbis = patternHistory("NBIS") || {};
  document.getElementById("proof").innerHTML =
    "<b>Is this proven? No.</b> Last year the pattern showed up on " + (spy.n || 0) + " days for SPY and " + (nbis.n || 0) +
    " for NBIS. That is too few to be sure it works. Use paper money until you have watched it work yourself.";
}

// ---------- Optional tools ----------

function lineChart(series, width, height, color) {
  if (!series.length) return "<p class='hint'>No price data.</p>";
  const closes = series.map((row) => row.close);
  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const pad = (max - min) * 0.05 || 1;
  const x = (i) => (i / (series.length - 1)) * (width - 8) + 4;
  const y = (v) => height - 8 - ((v - (min - pad)) / (max - min + 2 * pad)) * (height - 16);
  const points = series.map((row, i) => x(i).toFixed(1) + "," + y(row.close).toFixed(1)).join(" ");
  return '<svg viewBox="0 0 ' + width + " " + height + '" role="img" aria-label="price chart">' +
    '<polyline fill="none" stroke="' + color + '" stroke-width="1.6" points="' + points + '"/>' +
    '<text x="6" y="14" font-size="11" fill="#5d6d7e">high ' + num(max) + "</text>" +
    '<text x="6" y="' + (height - 10) + '" font-size="11" fill="#5d6d7e">low ' + num(min) + " · " +
    esc(series[0].date) + " to " + esc(series[series.length - 1].date) + "</text></svg>";
}

function histogram(values, width, height) {
  if (!values.length) return "<p class='hint'>No examples.</p>";
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
    rects += '<rect x="' + (i * bw + 1).toFixed(1) + '" y="' + (height - 18 - h).toFixed(1) + '" width="' + (bw - 2).toFixed(1) +
      '" height="' + h.toFixed(1) + '" fill="' + (mid >= 0 ? "#1e8449" : "#b03a2e") + '" opacity="0.75"><title>' + count +
      " times near " + pct(mid) + "</title></rect>";
  });
  const zeroX = ((0 - lo) / (hi - lo)) * width;
  return '<svg viewBox="0 0 ' + width + " " + height + '" role="img" aria-label="histogram">' + rects +
    '<line x1="' + zeroX.toFixed(1) + '" y1="2" x2="' + zeroX.toFixed(1) + '" y2="' + (height - 18) + '" stroke="#17202a" stroke-dasharray="3 3"/>' +
    '<text x="4" y="' + (height - 4) + '" font-size="11" fill="#5d6d7e">' + pct(lo) + "</text>" +
    '<text x="' + (width - 52) + '" y="' + (height - 4) + '" font-size="11" fill="#5d6d7e">' + pct(hi) + "</text></svg>";
}

function payoffAt(type, spot, shortStrike, longStrike, credit) {
  if (type === "put") return credit - Math.max(0, shortStrike - spot) + Math.max(0, longStrike - spot);
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
    '<polyline fill="none" stroke="#2456a6" stroke-width="2" points="' + points + '"/>' +
    '<text x="10" y="16" font-size="11" fill="#1e8449">most you make ' + money(maxProfit) + "</text>" +
    '<text x="10" y="' + (H - 8) + '" font-size="11" fill="#b03a2e">most you lose ' + money(maxLoss) + "</text>" +
    '<text x="' + Math.min(W - 140, x(shortStrike) + 4) + '" y="30" font-size="11" fill="#5d6d7e">sell strike ' + num(shortStrike, 0) + "</text></svg>";
}

function renderVerdicts() {
  const rows = (DATA.ranked_candidates || []).slice(0, 4);
  document.getElementById("verdicts").innerHTML = rows.map((row, index) => {
    const pill = row.n < 30 ? '<span class="pill small">' + row.n + " times · too few</span>" : '<span class="pill weak">' + row.n + " times</span>";
    return '<div class="verdict"><h3>' + (index + 1) + ". " + esc(row.symbol) + ": " + esc(FAMILY_LABEL[row.family] || row.family) +
      ", held " + row.horizon + " day" + (row.horizon > 1 ? "s" : "") + "</h3>" + pill +
      "<p>Went the seller's way " + pct(row.win_rate, 0) + " of the time</p>" +
      "<p>Moved too far by the close: " + pct(row.breach_close_rate, 0) + "</p></div>";
  }).join("");
  const direct = DATA.direct_summary || {};
  document.getElementById("directNote").textContent =
    "We could check real option prices 1-2 days later only " + (direct.marked || 0) + " times out of " +
    ((direct.marked || 0) + (direct.unmarked || 0)) + " tries, so these cards grade how the stock moved instead.";
}

function renderPrices(symbol) {
  document.querySelectorAll("[data-symbol]").forEach((btn) => btn.classList.toggle("active", btn.dataset.symbol === symbol));
  const series = (DATA.prices || {})[symbol] || [];
  document.getElementById("priceChart").innerHTML = lineChart(series, 720, 200, symbol === "SPY" ? "#2456a6" : "#7d3c98");
  const path = (DATA.pair_paths || []).find((row) => row.symbol === symbol) || {};
  document.getElementById("pathStats").textContent =
    "Up " + pct(path.simple_return, 0) + " for the year, but it fell as much as " + pct(path.max_drawdown, 0) + " along the way.";
}

function renderExplorer() {
  const symbol = document.getElementById("exSymbol").value;
  const family = document.getElementById("exFamily").value;
  const horizon = Number(document.getElementById("exHorizon").value);
  const rows = (DATA.windows || []).filter((row) => row.symbol === symbol && row.family === family && row.horizon === horizon);
  const summary = (DATA.window_summaries || []).find((row) => row.symbol === symbol && row.family === family && row.horizon === horizon) || {};
  const stat = (label, value) => '<div class="stat"><b>' + value + "</b><span>" + label + "</span></div>";
  document.getElementById("exStats").innerHTML =
    stat("times it showed up", String(summary.n || rows.length)) +
    stat("went the seller's way", pct(summary.win_rate, 0)) +
    stat("moved too far by the close", pct(summary.breach_close_rate, 0)) +
    stat("moved too far during the day", pct(summary.breach_intra_rate, 0));
  document.getElementById("exHist").innerHTML = histogram(rows.map((row) => row.signed_return), 720, 150);
  const shown = rows.slice().sort((a, b) => (a.signal_date < b.signal_date ? 1 : -1)).slice(0, 8);
  document.getElementById("exTable").innerHTML = shown.length
    ? "<table><tr><th>Day</th><th>Stock moved our way</th><th>Too far?</th></tr>" +
      shown.map((row) => "<tr><td>" + esc(row.signal_date) + "</td><td>" + pct(row.signed_return) + "</td><td>" +
        (row.breach_intra || row.breach_close ? "yes" : "no") + "</td></tr>").join("") + "</table>"
    : "";
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
  const stat = (label, value) => '<div class="stat"><b>' + value + "</b><span>" + label + "</span></div>";
  document.getElementById("pfStats").innerHTML =
    stat("you get paid now", money(maxProfit)) +
    stat("worst case", money(maxLoss)) +
    stat("take profit at", money(maxProfit / 2));
  document.getElementById("pfChart").innerHTML = widthStrike > 0 && credit > 0
    ? payoffChart(type, shortStrike, longStrike, credit, contracts)
    : '<p class="hint">Enter two different strikes and the money you get paid.</p>';
}

function renderVariants() {
  const family = document.getElementById("varFamily").value;
  const rows = (DATA.variants || []).filter((row) => family === "all" || row.family === family);
  document.getElementById("varTable").innerHTML =
    "<table><tr><th>Test</th><th>Checked</th><th>No price next day</th><th>Share checked</th></tr>" +
    rows.map((row) => {
      const total = (row.n || 0) + (row.unmarked_n || 0);
      const share = total ? row.n / total : 0;
      return "<tr><td>" + esc(row.variant) + "</td><td>" + row.n + "</td><td>" + row.unmarked_n +
        '</td><td><div class="bar"><i style="width:' + (share * 100).toFixed(1) + '%"></i></div></td></tr>';
    }).join("") + "</table>";
}

function preset(symbol) {
  fetch("live.json", { cache: "no-store" })
    .then((response) => response.json())
    .then((saved) => {
      const trade = ((saved.symbols || {})[symbol] || {}).trade;
      if (!trade) return;
      document.getElementById("pfType").value = trade.right === "PUT" ? "put" : "call";
      document.getElementById("pfShort").value = trade.short_strike;
      document.getElementById("pfLong").value = trade.long_strike;
      document.getElementById("pfCredit").value = Number(trade.credit).toFixed(2);
      renderPayoff();
    })
    .catch(() => {});
}

async function boot() {
  DATA = await (await fetch("data.json")).json();
  renderProof();
  loadAnswers();
  renderVerdicts();
  renderPrices("SPY");
  renderExplorer();
  renderPayoff();
  renderVariants();
  document.querySelectorAll("[data-symbol]").forEach((btn) => btn.addEventListener("click", () => renderPrices(btn.dataset.symbol)));
  ["exSymbol", "exFamily", "exHorizon"].forEach((id) => document.getElementById(id).addEventListener("change", renderExplorer));
  ["pfType", "pfShort", "pfLong", "pfCredit", "pfContracts"].forEach((id) => {
    document.getElementById(id).addEventListener("input", renderPayoff);
    document.getElementById(id).addEventListener("change", renderPayoff);
  });
  document.getElementById("presetSpy").addEventListener("click", () => preset("SPY"));
  document.getElementById("presetNbis").addEventListener("click", () => preset("NBIS"));
  document.getElementById("varFamily").addEventListener("change", renderVariants);
}

boot().catch((error) => {
  SYMBOLS.forEach((symbol) => {
    document.getElementById("card-" + symbol).innerHTML = '<p class="hint">The page could not load its data (' + esc(error.message) + ").</p>";
  });
});
