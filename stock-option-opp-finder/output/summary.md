# What the last year paid, 2025-11-10 through 2026-11-09

No listed-option strategy with at least 30 closed trades has a positive average R. The highest average is momentum_breakout at -0.304 (n=33). No stock-proxy strategy has a mean R whose normal 95% interval sits above zero. The highest positive average with at least 30 closed trades is mean_reversion: mean R 0.129, n=58, interval [-0.086, 0.344]. That interval includes zero, so this is a point estimate rather than a demonstrated edge. On the last completed session, no name matches a setup whose historical sample cleared 30 trades and a positive interval for mean R.

## The market behind the window

Prices run from 2024-06-03 so the 200-day average and the 252-day volatility percentile exist by 2025-11-10. The tested signals stop at 2026-11-09. Requested end was 2026-11-10. Session rule: requested end 2026-11-10 VIX file ends 2026-11-09 SPY download ends 2026-11-10 study sessions run through 2026-11-09

SPY adjusted close went from 681.44 on 2025-11-10 to 752.69 on 2026-11-09, a simple return of 10.5%. Of 251 SPY sessions in the test window, uptrend 238 (95%), range 13 (5%).

CBOE VIX in the window opened the first session at 17.60 and closed the last at 19.92. The high was 35.30 on 2026-03-09 and the low was 13.38 on 2025-12-24.

SPY vendor `iv_current` versus VIX/100 on 247 overlapping sessions: correlation 0.985, mean of (vendor IV minus VIX/100) -0.0313. They are related series, not the same number. Signals use the vendor IV, not a rescaled VIX.

Price history loaded for SPY, QQQ, IWM, AAPL, MSFT, NVDA, AMZN, META, GOOGL, TSLA, AMD, AVGO, NFLX, JPM, AMAT. Missing price history: none.
QQQ and IWM are in the stock book. The free option dataset returned no chain and no IV row for them, so they have no listed-vertical trades. VXN and RVX are used only as an index-IV proxy in the variance study.
Yahoo reported splits: NVDA 2024-06-10 10-for-1; AVGO 2024-07-15 10-for-1; NFLX 2025-11-17 10-for-1. Option trades that straddle a split are dropped.

## How a trade was counted

Signals use only the close they are stamped with. Stock proxies buy or sell the next session's open. Stops are 2 times the 14-day ATR. A stop touched intraday fills at the stop; a gap through the stop fills at the open. Both then take 5 bps of adverse slippage. Stock commission is zero. Each trade risks 1% of a $100,000 reference ($1,000). Size does not compound. One position per symbol per strategy.

Listed verticals are one strike wide on the DoltHub end-of-day grid. Debit spreads buy the leg nearest a 0.45 delta and sell the next further strike. Credit spreads sell the leg nearest a 0.30 delta and buy the next further strike. Natural prices: buy at the ask, sell at the bid. Commission is $0.65 per contract per leg per side. One contract is allowed up to 2.5% of the reference account; wider risk is skipped. The option entry is the end-of-day chain on the session after the signal, because that dataset has no open quotes. The option exit is the end-of-day chain on the session the stock rule exits, or up to two later sessions if those exact strikes are missing. Same-session option round trips are dropped. There is one quote per day, so it cannot be both the entry and the exit.

Trend continuation is a cross back through the 20-day average while the 50-day average is sloping with the trade and price is on that side of the 50-day. Hold is 15 sessions or until price closes back through the 50-day. Mean reversion buys a stretch in an uptrend: close above the 200-day, RSI(2) under 10, and close under the lower 20-day Bollinger band (2 standard deviations). The short is the mirror under the 200-day. Hold is 5 sessions or a cross back through the 20-day. Momentum breakout is a close through the prior 20-session high or low, with the 50-day on that side and volume above 1.2 times the prior 20-session average. Hold is 10 sessions or a close back through the broken level. High-IV premium selling requires an IV percentile of at least 0.60 inside the trailing 252 vendor readings and vendor IV above 20-day realized vol. Above the 50-day it sells a put vertical; below the 50-day it sells a call vertical. Hold is 15 sessions or an underlying close through the short strike.

Trend regime: uptrend when close and the 50-day are both above the 200-day; downtrend when both are below; otherwise range. Vol regime: high when 20-day realized vol is at or above the median of the prior 252 readings. Expectancy is the mean P&L, scratches included. Profit factor is gross wins over absolute gross losses, and it is undefined when there is no loss. R is P&L divided by the defined risk (stop risk for stock, theoretical vertical max loss for options). A normal 95% interval is reported only as a rough check. Below 30 closed trades the average is descriptive only.

## Listed option verticals

These are end-of-day bid/ask fills on one-strike verticals from the DoltHub chain. A missing exit quote is left unmarked. It is not replaced with a model price.

| Strategy | Trades | Win rate | Avg win | Avg loss | Expectancy | Mean R | Profit factor | Max DD | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| trend_continuation | 36 | 8.3% | $191.87 | $-435.30 | $-383.03 | -0.480 | 0.04 | 13.8% | negative_interval_below_zero |
| mean_reversion | 6 | 33.3% | $335.80 | $-410.90 | $-162.00 | -0.195 | 0.41 | 1.1% | too_small |
| high_iv_premium | 33 | 15.2% | $79.24 | $-435.80 | $-357.76 | -0.408 | 0.03 | 11.9% | negative_interval_below_zero |
| momentum_breakout | 33 | 15.2% | $442.88 | $-397.44 | $-270.12 | -0.304 | 0.20 | 9.2% | negative_interval_below_zero |

- **trend_continuation** (n=36): n=36. Mean R is negative and a normal 95% interval is below zero, with the same correlation caveat.
- **mean_reversion** (n=6): Sample is 6 closed trades, below 30. The point estimate is descriptive only and is not evidence of a repeatable edge.
- **high_iv_premium** (n=33): n=33. Mean R is negative and a normal 95% interval is below zero, with the same correlation caveat.
- **momentum_breakout** (n=33): n=33. Mean R is negative and a normal 95% interval is below zero, with the same correlation caveat.

## Stock proxies for the same signals

Same entry rules, but the fill is the stock: next-session open, a 2 ATR stop, and 5 bps of adverse slippage. This is not an option payoff. Premium selling has no stock-stop version, because a stop on the shares does not match a credit spread.

| Strategy | Trades | Win rate | Avg win | Avg loss | Expectancy | Mean R | Profit factor | Max DD | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| trend_continuation | 129 | 34.1% | $934.99 | $-738.33 | $-167.58 | -0.170 | 0.66 | 24.3% | negative_interval_includes_zero |
| mean_reversion | 58 | 62.1% | $665.21 | $-752.72 | $127.37 | 0.129 | 1.45 | 3.2% | positive_interval_includes_zero |
| momentum_breakout | 137 | 30.7% | $834.19 | $-570.54 | $-139.89 | -0.141 | 0.65 | 20.1% | negative_interval_below_zero |

- **trend_continuation** (n=129): n=129. The average R is negative in this sample, but the normal 95% interval includes zero.
- **mean_reversion** (n=58): n=58. The average R is positive in this sample, but the normal 95% interval includes zero. That is not enough to call the approach a winner.
- **momentum_breakout** (n=137): n=137. Mean R is negative and a normal 95% interval is below zero, with the same correlation caveat.

## Regimes

A trade keeps both labels, so the trend rows and the vol rows are two views of the same trades, not a partition. Slices under 30 trades stay descriptive.

| Book | Strategy | Slice | Trades | Mean R | Expectancy | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| direct_option | trend_continuation | uptrend | 30 | -0.468 | $-366.77 | negative_interval_below_zero |
| direct_option | trend_continuation | downtrend | 3 | -0.608 | $-560.07 | too_small |
| direct_option | trend_continuation | high_vol | 19 | -0.573 | $-464.99 | too_small |
| direct_option | trend_continuation | low_vol | 17 | -0.376 | $-291.44 | too_small |
| direct_option | mean_reversion | uptrend | 4 | 0.018 | $27.50 | too_small |
| direct_option | mean_reversion | downtrend | 2 | -0.620 | $-541.00 | too_small |
| direct_option | mean_reversion | high_vol | 3 | -0.480 | $-418.27 | too_small |
| direct_option | mean_reversion | low_vol | 3 | 0.091 | $94.27 | too_small |
| direct_option | high_iv_premium | uptrend | 24 | -0.345 | $-305.23 | too_small |
| direct_option | high_iv_premium | downtrend | 6 | -0.461 | $-428.80 | too_small |
| direct_option | high_iv_premium | high_vol | 16 | -0.395 | $-364.06 | too_small |
| direct_option | high_iv_premium | low_vol | 17 | -0.419 | $-351.84 | too_small |
| direct_option | momentum_breakout | uptrend | 23 | -0.342 | $-300.91 | too_small |
| direct_option | momentum_breakout | downtrend | 8 | -0.249 | $-228.03 | too_small |
| direct_option | momentum_breakout | high_vol | 18 | -0.244 | $-210.12 | too_small |
| direct_option | momentum_breakout | low_vol | 15 | -0.376 | $-342.11 | too_small |
| underlying_proxy | trend_continuation | uptrend | 97 | -0.172 | $-169.95 | negative_interval_includes_zero |
| underlying_proxy | trend_continuation | downtrend | 20 | -0.237 | $-234.46 | too_small |
| underlying_proxy | trend_continuation | high_vol | 70 | -0.186 | $-182.46 | negative_interval_includes_zero |
| underlying_proxy | trend_continuation | low_vol | 59 | -0.151 | $-149.93 | negative_interval_includes_zero |
| underlying_proxy | mean_reversion | uptrend | 52 | 0.132 | $130.21 | positive_interval_includes_zero |
| underlying_proxy | mean_reversion | downtrend | 6 | 0.106 | $102.81 | too_small |
| underlying_proxy | mean_reversion | high_vol | 26 | 0.314 | $308.96 | too_small |
| underlying_proxy | mean_reversion | low_vol | 32 | -0.021 | $-20.17 | negative_interval_includes_zero |
| underlying_proxy | momentum_breakout | uptrend | 86 | -0.194 | $-191.33 | negative_interval_below_zero |
| underlying_proxy | momentum_breakout | downtrend | 32 | -0.099 | $-97.85 | negative_interval_includes_zero |
| underlying_proxy | momentum_breakout | high_vol | 78 | -0.119 | $-117.15 | negative_interval_includes_zero |
| underlying_proxy | momentum_breakout | low_vol | 59 | -0.171 | $-169.95 | negative_interval_includes_zero |

## Implied vol versus the vol that followed

**Vendor IV on names with a chain history** — 111 non-overlapping 15-session windows. This compares a volatility reading with the realized volatility that followed. It is not a spread P&L, and the vendor IV tenor is not documented in the source table, so a positive gap is a sign check rather than a matched-tenor variance swap. Mean IV 0.4109, mean forward realized vol 0.4018, mean IV minus realized 0.0091 vol points, mean of IV squared minus realized vol squared -0.0185, fraction with realized below implied 62.2%, fraction of underlying moves inside the one-standard-deviation expected move 64.0%, fraction with an adverse move beyond that band 20.7%.

**VXN for QQQ and RVX for IWM, divided by 100 (index proxy, not a fill)** — 20 non-overlapping 15-session windows. This compares a volatility reading with the realized volatility that followed. It is not a spread P&L, and the vendor IV tenor is not documented in the source table, so a positive gap is a sign check rather than a matched-tenor variance swap. Mean IV 0.2550, mean forward realized vol 0.2085, mean IV minus realized 0.0465 vol points, mean of IV squared minus realized vol squared 0.0183, fraction with realized below implied 80.0%, fraction of underlying moves inside the one-standard-deviation expected move 80.0%, fraction with an adverse move beyond that band 10.0%.

## Unmarked option exits

When the exit chain did not contain the same strikes within two sessions, the trade is excluded from expectancy. The underlying return over that intended hold is still real, and it shows whether the missing quotes were the large moves.
- **trend_continuation**: unmarked n=60, mean underlying return -0.9%; marked closed option trades n=36, mean underlying return -0.6%.
- **mean_reversion**: unmarked n=27, mean underlying return 0.1%; marked closed option trades n=6, mean underlying return 1.6%.
- **high_iv_premium**: unmarked n=79, mean underlying return 2.3%; marked closed option trades n=33, mean underlying return 0.8%.
- **momentum_breakout**: unmarked n=73, mean underlying return 0.1%; marked closed option trades n=33, mean underlying return 1.6%.

## Current scan

No last-session signal matches a book with a positive mean-R interval and at least 30 closed trades.

Other last-session patterns, with the historical sample beside them:

- **AAPL trend_continuation long** (direct_option, n=36, mean R -0.480, negative_interval_below_zero). close_above_sma50 (close 350.69 vs SMA50 336.63); sma50_rising (SMA50 336.63 vs SMA50 20 sessions ago 323.03); cross_above_sma20 (prior close 342.37 vs prior SMA20 343.38; close 350.69 vs SMA20 343.87). Invalidation: Close back below the 50-day average (336.63). Risk: Stock proxy risk is 1% of $100,000 ($1,000) with a 2 ATR stop (ATR14 is 8.86). Illustrated one-lot vertical max loss is $260.00 before commissions (debit call, width 5.00, premium 2.60). Pass if: Pass if the next open is already through the 2 ATR stop (ATR14 8.86), if the close is no longer on the signal side of the 50-day average, or if the entry chain cannot build a one-strike debit vertical inside the risk budget. Illustrated debit call 355.00/360.00 expiring 2026-12-18, premium 2.60, width 5.00. Illustration uses the signal session's end-of-day chain. The backtest would enter on the next session's chain, which is not a completed print yet.
- **MSFT trend_continuation long** (direct_option, n=36, mean R -0.480, negative_interval_below_zero). close_above_sma50 (close 545.18 vs SMA50 517.28); sma50_rising (SMA50 517.28 vs SMA50 20 sessions ago 501.98); cross_above_sma20 (prior close 530.61 vs prior SMA20 531.41; close 545.18 vs SMA20 531.61). Invalidation: Close back below the 50-day average (517.28). Risk: Stock proxy risk is 1% of $100,000 ($1,000) with a 2 ATR stop (ATR14 is 15.60). Illustrated one-lot vertical max loss is $405.00 before commissions (debit call, width 5.00, premium 4.05). Pass if: Pass if the next open is already through the 2 ATR stop (ATR14 15.60), if the close is no longer on the signal side of the 50-day average, or if the entry chain cannot build a one-strike debit vertical inside the risk budget. Illustrated debit call 555.00/560.00 expiring 2026-12-24, premium 4.05, width 5.00. Illustration uses the signal session's end-of-day chain. The backtest would enter on the next session's chain, which is not a completed print yet.
- **NVDA high_iv_premium short** (direct_option, n=33, mean R -0.408, negative_interval_below_zero). iv_percentile (IV percentile 1.00 vs minimum 0.60); iv_above_realized (IV 0.5760 vs 20-day realized vol 0.4923); close_below_sma50 (close 178.67 vs SMA50 219.04). Invalidation: Underlying close through the short strike of the credit vertical. That strike is chosen from the entry chain, not from this signal bar. Risk: There is no stock-stop version of premium selling in this test. Illustrated one-lot vertical max loss is $400.00 before commissions (credit call, width 5.00, premium 1.00). Pass if: Pass if IV percentile is back under 0.60, if IV is no longer above 20-day realized vol, if the underlying is already through the short strike, or if one contract's width-minus-credit loss exceeds 2.5% of the $100,000 reference. Illustrated credit call 205.00/200.00 expiring 2026-12-18, premium 1.00, width 5.00. Illustration uses the signal session's end-of-day chain. The backtest would enter on the next session's chain, which is not a completed print yet.
- **NVDA momentum_breakout short** (direct_option, n=33, mean R -0.304, negative_interval_below_zero). close_below_prior_20_low (close 178.67 vs prior 20-session low 181.46); close_below_sma50 (close 178.67 vs SMA50 219.04); volume_expansion (volume 462719300 vs 1.2x prior 20-session average 117698865). Invalidation: Close back through the broken 20-session level (181.46). Risk: Stock proxy risk is 1% of $100,000 ($1,000) with a 2 ATR stop (ATR14 is 8.39). Illustrated one-lot vertical max loss is $260.00 before commissions (debit put, width 5.00, premium 2.60). Pass if: Pass if price is back through 181.46 before entry, if the next open gaps through the 2 ATR stop, or if the entry chain has no one-strike debit vertical inside the risk budget. Illustrated debit put 180.00/175.00 expiring 2026-12-04, premium 2.60, width 5.00. Illustration uses the signal session's end-of-day chain. The backtest would enter on the next session's chain, which is not a completed print yet.

## Sentiment

News and positioning sources were called. A failed call is left blank. No score was filled in.
- GDELT DOC timelinetone: HTTP 429: Too Many Requests
- CNN Fear and Greed: HTTP 418: Unknown Error
- CBOE equity put/call: file downloaded; last date 2019-10-04. Not used unless that date reaches the study.
- CBOE total put/call: file downloaded; last date 2019-10-04. Not used unless that date reaches the study.
No source covered at least 80% of the SPY sessions in the test window, so no sentiment filter was applied.

## What can make this misleading

The chain is not the full listed book. Each snapshot in this dataset is a sampled strike grid and a handful of expirations. A strike that exists on entry can be absent after a large move, because the grid is recentered on spot. Dropping those exits can remove the very trades where a debit spread paid or a credit spread was run over. The unmarked-versus-marked underlying returns above are the check on that bias. They are not option P&L.

Stock fills use the next open. Option fills use an end-of-day quote on that same session, or on the exit session. Those clocks differ by hours. Intraday option stops are not visible. Assignment is not modeled. Early profit-taking at a fixed fraction of the credit was not tested, because that would require a chain every day.

Names in this universe move together. A t-statistic that treats trades as independent overstates the evidence, even when the interval is above zero. Drawdown for options is the closed-trade equity curve, not a daily mark.

Chain lookups that resolved: ok 1306, empty 22, network errors 0. Cache hits are included in the ok and empty counts (1303 hits). Data-source errors recorded: 0.

Top skip reasons: high_iv_premium|no_wing 24; high_iv_premium|no_short_leg 15; high_iv_premium|open_at_sample_end 9; mean_reversion|no_wing 7; trend_continuation|no_wing 7; high_iv_premium|entry_chain_empty 5; high_iv_premium|nonpositive_credit 5; momentum_breakout|debit_too_wide 5.

## Reproduce

From `stock-option-opp-finder`:

```
python3 -m oppfinder
python3 -m pytest
```

The run writes `output/trades.csv`, `output/stats.json`, `output/scan.json`, `output/vrp.csv`, and `output/summary.md`. Cached downloads live in `data/`. This is research, not a recommendation to trade.
