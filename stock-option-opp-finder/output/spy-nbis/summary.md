# SPY and NBIS, 2025-11-10 through 2026-11-10

Buy-and-hold over this one window: SPY 10.0% from 681.44 to 749.92; NBIS 21.9% from 109.95 to 134.00. One path is not a strategy sample. No stock-proxy strategy reached 30 closed trades. Averages in that book are descriptive only. None is treated as a winner. No listed-option strategy reached 30 closed trades. Averages in that book are descriptive only. None is treated as a winner. No non-overlapping signal window reached 30 observations with a positive interval for the signed close-to-close return. Those windows are a drift check, not a filled trade.

## The two paths

Session rule: requested end 2026-11-10 VIX file ends 2026-11-10 SPY download ends 2026-11-11 study sessions run through 2026-11-10

| Symbol | Sessions | Return | Max DD | Realized vol | Avg shares | Avg dollars |
| --- | --- | --- | --- | --- | --- | --- |
| SPY | 252 | 10.0% | 9.1% | 13.7% | 63,392,933 | $44,915,366,290 |
| NBIS | 252 | 21.9% | 58.0% | 109.4% | 18,307,921 | $3,040,566,801 |

SPY trend labels: uptrend 239 (95%), range 13 (5%). Vol labels: low_vol 134 (53%), high_vol 118 (47%).

NBIS trend labels: uptrend 234 (93%), range 18 (7%). Vol labels: unknown 8 (3%), high_vol 149 (59%), low_vol 95 (38%).

On 252 shared sessions, NBIS daily simple returns versus SPY: correlation 0.464, beta 3.77. Beta is the covariance divided by SPY's variance. It is a description of this window.

## Managed trades

Same rules as the full book: next-session open, a 2 ATR stop, 5 bps of adverse slippage, and 1% of a $100,000 reference per trade. One position per symbol per strategy. Below 30 closed trades the average is descriptive only.

| Symbol | Strategy | Trades | Win rate | Expectancy | Mean R | Profit factor | Max DD | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NBIS | trend_continuation | 7 | 28.6% | $155.41 | 0.156 | 1.30 | 2.2% | too_small |
| NBIS | mean_reversion | 4 | 75.0% | $345.35 | 0.349 | 5.22 | 0.3% | too_small |
| NBIS | momentum_breakout | 16 | 25.0% | $-284.54 | -0.291 | 0.21 | 4.6% | too_small |
| SPY | trend_continuation | 15 | 20.0% | $-375.19 | -0.377 | 0.18 | 5.6% | too_small |
| SPY | mean_reversion | 7 | 85.7% | $440.42 | 0.444 | 4.12 | 0.9% | too_small |
| SPY | momentum_breakout | 7 | 28.6% | $-346.09 | -0.349 | 0.16 | 2.4% | too_small |

## Drift after the same signals

Each row is the signed percent change from the signal close to the close a fixed number of sessions later. A short signal that falls is a positive signed return. There is no stop, no slippage, and no commission. Rows marked overlapping share days, so that label is not a significance test. The evidence words apply only to the non-overlapping rows.

| Symbol | Signal | Hold | Overlap | N | Mean signed | Win rate | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SPY | trend_continuation | 15 | non overlapping | 9 | -0.8% | 44.4% | too_small |
| SPY | trend_continuation | 15 | overlapping | 18 | -0.7% | 38.9% | overlapping |
| SPY | mean_reversion | 5 | non overlapping | 8 | 0.9% | 62.5% | too_small |
| SPY | mean_reversion | 5 | overlapping | 11 | 1.0% | 63.6% | overlapping |
| SPY | momentum_breakout | 10 | non overlapping | 4 | -2.5% | 25.0% | too_small |
| SPY | momentum_breakout | 10 | overlapping | 8 | -1.9% | 25.0% | overlapping |
| SPY | high_iv_premium | 15 | non overlapping | 9 | -0.5% | 55.6% | too_small |
| SPY | high_iv_premium | 15 | overlapping | 71 | -1.1% | 50.7% | overlapping |
| NBIS | trend_continuation | 15 | non overlapping | 6 | 10.6% | 66.7% | too_small |
| NBIS | trend_continuation | 15 | overlapping | 10 | 2.0% | 40.0% | overlapping |
| NBIS | mean_reversion | 5 | non overlapping | 4 | 14.1% | 50.0% | too_small |
| NBIS | mean_reversion | 5 | overlapping | 5 | 11.2% | 40.0% | overlapping |
| NBIS | momentum_breakout | 10 | non overlapping | 12 | -7.0% | 33.3% | too_small |
| NBIS | momentum_breakout | 10 | overlapping | 22 | -10.0% | 36.4% | overlapping |

## Listed SPY verticals and the NBIS option gap

NBIS has 0 rows in DoltHub volatility_history. option_chain on 2026-11-06 also returned 0 rows. Listed verticals were not backtested. The stock rules and the close-to-close drift are what ran.

SPY verticals use the end-of-day bid and ask on the sampled strike grid. A missing exit quote stays missing.

| Symbol | Strategy | Trades | Win rate | Expectancy | Mean R | Profit factor | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SPY | trend_continuation | 2 | 100.0% | $113.00 | 0.126 | undefined | too_small |

Unmarked exits, compared on the underlying return over the intended hold:
- trend_continuation: unmarked n=13, mean underlying -0.8%; marked n=2, mean underlying 0.8%.
- mean_reversion: unmarked n=7, mean underlying 0.5%; marked n=0, mean underlying n/a.
- high_iv_premium: unmarked n=9, mean underlying 0.9%; marked n=0, mean underlying n/a.
- momentum_breakout: unmarked n=7, mean underlying 0.6%; marked n=0, mean underlying n/a.

Vendor IV on names with a chain history: 9 non-overlapping 15-session windows. This compares a volatility reading with the realized volatility that followed. It is not a spread P&L, and the vendor IV tenor is not documented in the source table, so a positive gap is a sign check rather than a matched-tenor variance swap. Mean IV minus forward realized vol 0.0427. Mean of IV squared minus realized vol squared 0.0145. Fraction with realized vol below IV 88.9%.

## What is on the board now

Neither name matched a rule on the last completed session.

## Sentiment

A sentiment score is used only when a free source covers the window. Failed calls stay blank.
- GDELT DOC timelinetone: HTTP 429: Too Many Requests
- CNN Fear and Greed: HTTP 418: Unknown Error
- CBOE equity put/call: file downloaded; last date 2019-10-04. Not used unless that date reaches the study.
- CBOE total put/call: file downloaded; last date 2019-10-04. Not used unless that date reaches the study.
No sentiment filter was applied.

## How to read this

Downloaded history starts at the first Yahoo bar: SPY 2024-06-03; NBIS 2024-10-21. Indicators that need more bars than that history stay blank until they exist.

The four rules were fixed before this pair was run. Nothing in this report was chosen by searching thresholds. Two names in one year do not produce a large independent sample, and NBIS moves with the same market as SPY.

Chain lookups: ok 150, empty 0, errors 0.

Top skip reasons: high_iv_premium|open_at_sample_end 1.

This is research, not a recommendation to trade. The names in this run: SPY, NBIS.
