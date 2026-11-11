# Stock and option opportunity finder

Research backtest of liquid US stocks and listed option verticals from 2025-11-10 through the latest completed session on or before 2026-11-10. It compares four rules, keeps missing option quotes missing, and writes a current scan.

This is research, not a recommendation to trade. Past results in this sample are not a forecast.

This directory is part of the AI-Projects repository and is covered by the repository's AGPL-3.0 license.

## Run

```bash
cd stock-option-opp-finder
python3 -m oppfinder
python3 -m pytest
```

The runner uses the Python standard library only. Tests need `pytest` (`pip install -r requirements.txt`).

Cached downloads live in `data/`. Delete that directory, or pass `--refresh`, to call the sources again. `--findings PATH` also writes the long report.

A two-name run keeps the same rules and writes its own folder:

```bash
python3 -m oppfinder --symbols SPY,NBIS --output output/spy-nbis
```

NBIS is included only when that command is used. If the free option dataset has no rows for a symbol, the run says so and prices the stock rules only.

The 1-2 session premium study is a separate entrypoint. It marks SPY credit verticals at the exact next end-of-day chain, and reports how often that quote is simply absent:

```bash
python3 -m oppfinder.short_premium_run
```

## What it tests

Universe: SPY, QQQ, IWM, AAPL, MSFT, NVDA, AMZN, META, GOOGL, TSLA, AMD, plus AVGO, NFLX, JPM, and AMAT because those four are liquid option underlyings and the free chain history actually contains them.

| Book | What the P&L is |
| --- | --- |
| Listed verticals | One-strike debit or credit spreads, filled at the published bid and ask |
| Stock proxy | The same directional signals on the shares, with a 2 ATR stop |
| Variance study | Vendor or index implied vol versus the realized vol that followed. Not a P&L |

QQQ and IWM are in the stock book only. The free chain dataset has no rows for them. Premium selling has no stock-stop version: a stop on the shares is a different payoff.

Rules, fixed before looking at P&L:

- Trend continuation: cross back through the 20-day average while the 50-day average slopes with the trade. Hold 15 sessions, or exit after a close back through the 50-day.
- Mean reversion: in an uptrend (above the 200-day), RSI(2) under 10 and close under the lower Bollinger band. The short is the mirror. Hold 5 sessions, or exit on a cross back through the 20-day.
- Momentum breakout: close through the prior 20-session high or low, 50-day on that side, volume above 1.2 times its prior 20-session average. Hold 10 sessions, or exit on a close back through the level.
- High-IV premium: IV percentile at least 0.60 and IV above 20-day realized vol. Sell a put vertical above the 50-day, or a call vertical below it. Hold 15 sessions, or exit if the underlying closes through the short strike.

Stock orders go in at the next open. Option orders use the end-of-day chain on that next session, because the historical file has no open quotes. Each trade risks 1% of a $100,000 reference ($1,000) and does not compound. Stock slippage is 5 bps per fill. Option commission is $0.65 per contract per leg per side, and the bid/ask is paid. One contract is allowed up to 2.5% of the reference; larger max loss is skipped.

## Data

- Daily OHLC: Yahoo Finance chart API.
- VIX, VXN, RVX, VIX3M: CBOE daily index files.
- End-of-day option quotes, greeks, and a vendor IV field: [DoltHub `post-no-preference/options`](https://www.dolthub.com/repositories/post-no-preference/options), table `option_chain` and `volatility_history`. Queries are one symbol and one exact chain date, which is what that API will answer. The chain is a sampled strike grid, not the full book.
- Sentiment probes: GDELT DOC tone, CNN Fear and Greed, and the public CBOE put/call CSV. A source is used only when the call parses and covers the window. Failed calls stay failed.

## Outputs

- `output/trades.csv` — closed and still-open trades
- `output/stats.json` — expectancy, drawdown, regimes, skips, errors
- `output/vrp.csv` — non-overlapping IV versus subsequent realized vol
- `output/scan.json` — last-session pattern matches
- `output/summary.md` — the written results

A strategy is called supported only when it has at least 30 closed trades and the rough 95% interval for mean R is above zero. Smaller samples stay in the tables as descriptions.

## Tests

`python3 -m pytest` covers expectancy, drawdown, regime labels, the no-lookahead property of the indicators, spread construction, and the rule that a small sample is not crowned. Network calls are not part of the tests.
