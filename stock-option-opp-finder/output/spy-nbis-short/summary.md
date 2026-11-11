# SPY and NBIS premium selling for 1-3 sessions, 2025-11-10 through 2026-11-10

Across 18 variants, the free historical chain marked 5 SPY credit-vertical closes at the exact 1- or 2-session exit; 319 variant entries were unmarked because that day's sampled chain had no quote for the same strikes. The sampled grid rotates strikes and expirations daily. A sample that small cannot name a winnable option strategy, and the marked trades are the ones whose strikes happened to survive, so their average is not the strategy's average.

The ranking below therefore uses two lower tiers of evidence: the few marked SPY verticals, and what SPY and NBIS themselves did in the 1-3 sessions after the same signals (signed drift, worst adverse move versus the expected move at the signal). The second tier is a risk proxy for selling a defined-risk vertical. It is not option P&L, and for NBIS there is no historical option test at all.

The only family with at least 30 windows is SPY high_iv, held 3 sessions: n=77, mean signed underlying return -0.0%, win rate 54.5%, adverse intraday move beyond the expected move in 29.9% of windows. That is not a friendly premium-selling profile. The 1- and 2-session rows for that same family are in the table. The friendlier patterns in the table have 5-20 windows and are descriptive only.

No family signal fired on the last completed session (2026-11-10).

## Direct SPY credit verticals, held 1-2 sessions

Entry is the end-of-day chain on the session after the signal. Exit is that chain exactly 1 or 2 sessions later, or the first session when the closing debit is at most half the credit (pt50_by_day2). Near expiries target 14 days (5-25 allowed); monthly targets 35 (25-55). The dataset's nearest SPY expiry is usually about two weeks out, so no 0-2 day expiry was tested. Commission is $0.65 per contract per leg per side and the bid/ask is paid. These 18 variants are a multiple-comparison set: a positive average in one row is not a discovery.

| Variant | Marked | Unmarked | Win rate | Expectancy | Mean R | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| high_iv_hold1_near | 1 | 30 | 0.0% | $-11.20 | -0.011 | too_small |
| high_iv_hold2_monthly | 1 | 25 | 0.0% | $-10.60 | -0.019 | too_small |
| high_iv_pt50_by_day2_monthly | 1 | 25 | 0.0% | $-10.60 | -0.019 | too_small |
| high_iv_hold1_monthly | 2 | 29 | 0.0% | $-53.40 | -0.068 | too_small |
| high_iv_hold2_near | 0 | 26 | n/a | n/a | n/a | too_small |
| high_iv_pt50_by_day2_near | 0 | 26 | n/a | n/a | n/a | too_small |
| mr_fade_hold1_near | 0 | 8 | n/a | n/a | n/a | too_small |
| mr_fade_hold1_monthly | 0 | 8 | n/a | n/a | n/a | too_small |
| mr_fade_hold2_near | 0 | 8 | n/a | n/a | n/a | too_small |
| mr_fade_hold2_monthly | 0 | 8 | n/a | n/a | n/a | too_small |
| mr_fade_pt50_by_day2_near | 0 | 8 | n/a | n/a | n/a | too_small |
| mr_fade_pt50_by_day2_monthly | 0 | 8 | n/a | n/a | n/a | too_small |
| trend_aligned_hold1_near | 0 | 19 | n/a | n/a | n/a | too_small |
| trend_aligned_hold1_monthly | 0 | 19 | n/a | n/a | n/a | too_small |
| trend_aligned_hold2_near | 0 | 18 | n/a | n/a | n/a | too_small |
| trend_aligned_hold2_monthly | 0 | 18 | n/a | n/a | n/a | too_small |
| trend_aligned_pt50_by_day2_near | 0 | 18 | n/a | n/a | n/a | too_small |
| trend_aligned_pt50_by_day2_monthly | 0 | 18 | n/a | n/a | n/a | too_small |

## What the underlying did after the same signals

Overlapping windows after each signal in the study year. A bullish credit wants the signed return near or above zero and the adverse move inside the expected move implied at the signal (vendor IV for SPY, 20-day realized vol where a name has no IV). Intraday breach uses the worst high or low in the window, which is the path a short vertical actually has to survive.

| Symbol | Family | Hold | N | Mean signed | Win rate | Adverse close > expected move | Adverse intraday > expected move | IV minus forward RV |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SPY | high_iv | 1 | 77 | -0.1% | 40.3% | 13.0% | 29.9% | 0.0609 |
| SPY | high_iv | 2 | 77 | -0.1% | 44.2% | 22.1% | 32.5% | 0.0340 |
| SPY | high_iv | 3 | 77 | -0.0% | 54.5% | 18.2% | 29.9% | 0.0239 |
| SPY | mr_fade | 1 | 11 | 0.8% | 81.8% | 0.0% | 9.1% | 0.0356 |
| SPY | mr_fade | 2 | 11 | 1.3% | 81.8% | 0.0% | 0.0% | 0.0365 |
| SPY | mr_fade | 3 | 11 | 1.4% | 72.7% | 9.1% | 9.1% | 0.0089 |
| SPY | trend_aligned | 1 | 20 | -0.0% | 45.0% | 15.0% | 20.0% | 0.0506 |
| SPY | trend_aligned | 2 | 20 | -0.1% | 45.0% | 20.0% | 30.0% | 0.0311 |
| SPY | trend_aligned | 3 | 20 | -0.1% | 50.0% | 20.0% | 50.0% | 0.0322 |
| NBIS | mr_fade | 1 | 5 | 5.8% | 80.0% | 0.0% | 40.0% | n/a |
| NBIS | mr_fade | 2 | 5 | 8.3% | 60.0% | 20.0% | 20.0% | n/a |
| NBIS | mr_fade | 3 | 5 | 14.9% | 80.0% | 20.0% | 20.0% | n/a |
| NBIS | trend_aligned | 1 | 10 | 2.8% | 50.0% | 0.0% | 0.0% | n/a |
| NBIS | trend_aligned | 2 | 10 | 2.7% | 70.0% | 10.0% | 10.0% | n/a |
| NBIS | trend_aligned | 3 | 10 | 7.6% | 70.0% | 10.0% | 10.0% | n/a |

## Ranking

Ranked as premium-selling candidates, best first, using the proxy table. None of these is a demonstrated option edge:

1. **NBIS mr_fade, 1 session(s)** - n=5 (under 30 windows, descriptive), mean signed 5.8%, win rate 80.0%, adverse close beyond expected move 0.0%, adverse intraday beyond expected move 40.0%.
2. **NBIS trend_aligned, 1 session(s)** - n=10 (under 30 windows, descriptive), mean signed 2.8%, win rate 50.0%, adverse close beyond expected move 0.0%, adverse intraday beyond expected move 0.0%.
3. **SPY mr_fade, 2 session(s)** - n=11 (under 30 windows, descriptive), mean signed 1.3%, win rate 81.8%, adverse close beyond expected move 0.0%, adverse intraday beyond expected move 0.0%.
4. **SPY mr_fade, 1 session(s)** - n=11 (under 30 windows, descriptive), mean signed 0.8%, win rate 81.8%, adverse close beyond expected move 0.0%, adverse intraday beyond expected move 9.1%.
5. **SPY mr_fade, 3 session(s)** - n=11 (under 30 windows, descriptive), mean signed 1.4%, win rate 72.7%, adverse close beyond expected move 9.1%, adverse intraday beyond expected move 9.1%.
6. **NBIS trend_aligned, 3 session(s)** - n=10 (under 30 windows, descriptive), mean signed 7.6%, win rate 70.0%, adverse close beyond expected move 10.0%, adverse intraday beyond expected move 10.0%.
7. **NBIS trend_aligned, 2 session(s)** - n=10 (under 30 windows, descriptive), mean signed 2.7%, win rate 70.0%, adverse close beyond expected move 10.0%, adverse intraday beyond expected move 10.0%.
8. **SPY high_iv, 1 session(s)** - n=77, mean signed -0.1%, win rate 40.3%, adverse close beyond expected move 13.0%, adverse intraday beyond expected move 29.9%.
9. **SPY trend_aligned, 1 session(s)** - n=20 (under 30 windows, descriptive), mean signed -0.0%, win rate 45.0%, adverse close beyond expected move 15.0%, adverse intraday beyond expected move 20.0%.
10. **SPY high_iv, 3 session(s)** - n=77, mean signed -0.0%, win rate 54.5%, adverse close beyond expected move 18.2%, adverse intraday beyond expected move 29.9%.
11. **NBIS mr_fade, 3 session(s)** - n=5 (under 30 windows, descriptive), mean signed 14.9%, win rate 80.0%, adverse close beyond expected move 20.0%, adverse intraday beyond expected move 20.0%.
12. **NBIS mr_fade, 2 session(s)** - n=5 (under 30 windows, descriptive), mean signed 8.3%, win rate 60.0%, adverse close beyond expected move 20.0%, adverse intraday beyond expected move 20.0%.
13. **SPY trend_aligned, 2 session(s)** - n=20 (under 30 windows, descriptive), mean signed -0.1%, win rate 45.0%, adverse close beyond expected move 20.0%, adverse intraday beyond expected move 30.0%.
14. **SPY trend_aligned, 3 session(s)** - n=20 (under 30 windows, descriptive), mean signed -0.1%, win rate 50.0%, adverse close beyond expected move 20.0%, adverse intraday beyond expected move 50.0%.
15. **SPY high_iv, 2 session(s)** - n=77, mean signed -0.1%, win rate 44.2%, adverse close beyond expected move 22.1%, adverse intraday beyond expected move 32.5%.

What this means in trade terms: the structure worth paper-testing first is a defined-risk credit vertical after a mean-reversion stretch (sell the put vertical on a bullish stretch, the call vertical on a bearish one), sized at the same 1% defined risk, closed by the third session or at half the credit, whichever comes first. High-IV selling without a stretch had the largest sample and the weakest drift in this table. Anything on NBIS is unpriced historically, so it cannot rank as a tested strategy.

## Current snapshot (not a backtest)

Source: Robinhood read-only market quotes fetched 2026-11-11. Current snapshot only; not a backtest fill. As of 2026-11-11T16:02:46Z.

- SPY last 758.22 versus the 2026-11-10 close 749.92 (1.1%).
- NBIS last 156.67 versus the 2026-11-10 close 134.00 (16.9%).

Nearest expirations: SPY 2026-11-11, 2026-11-12, 2026-11-13; NBIS 2026-11-13, 2026-11-20, 2026-11-27.

| Symbol | Expiry | Put strike | Bid | Ask | IV | Delta | Open interest |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SPY | 2026-11-13 | 755 | 2.12 | 2.14 | 15.5% | -0.346 | 9753 |
| SPY | 2026-11-13 | 750 | 1.10 | 1.11 | 17.2% | -0.196 | 9733 |
| SPY | 2026-11-13 | 745 | 0.58 | 0.59 | 18.9% | -0.109 | 29537 |
| SPY | 2026-11-13 | 740 | 0.31 | 0.32 | 20.6% | -0.060 | 22893 |
| NBIS | 2026-11-13 | 155 | 9.10 | 9.25 | 208.0% | -0.440 | 539 |
| NBIS | 2026-11-13 | 150 | 6.85 | 6.95 | 208.8% | -0.362 | 1379 |
| NBIS | 2026-11-13 | 145 | 4.95 | 5.05 | 209.3% | -0.287 | 821 |
| NBIS | 2026-11-13 | 140 | 3.45 | 3.55 | 210.3% | -0.220 | 1075 |

Illustrated from those quotes, SPY 2026-11-13: sell the 755 put at 2.12, buy the 750 put at 1.11. Credit 1.01, width 5, max loss $399 per contract before commissions. This is a current quote snapshot, not a fill and not a recommendation.

Illustrated from those quotes, NBIS 2026-11-13: sell the 145 put at 4.95, buy the 140 put at 3.55. Credit 1.40, width 5, max loss $360 per contract before commissions. This is a current quote snapshot, not a fill and not a recommendation.

## NBIS

NBIS has 0 rows in the free historical volatility table and 0 option-chain rows on 2026-11-06, and Yahoo's current-options endpoint returned HTTP 401 in this run. The current NBIS quotes in the snapshot above come from a read-only broker quote feed fetched for this report. They describe today's chain (nearest expiry 2026-11-13, put IV 208.0% to 210.3% at the quoted strikes). They cannot backtest anything.

So the honest NBIS answer is narrower: the stock's own 1-3 session behavior after stretch and trend signals is in the proxy table, and its realized vol over the study year was about 109% with a 58% max drawdown in the earlier pair study. Premium on NBIS is large because the moves are large. Until a historical NBIS chain is available, any NBIS premium structure is an untested candidate for paper trading at defined risk, not a ranked strategy.

This is research, not a recommendation to trade.
