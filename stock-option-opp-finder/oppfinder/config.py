"""Fixed study choices. These were set before looking at strategy P&L."""

from datetime import date
from decimal import Decimal

STUDY_START = date(2025, 11, 10)
STUDY_END = date(2026, 11, 10)
WARMUP_START = date(2024, 6, 3)

# Required names, plus four liquid option underlyings that the free chain
# dataset actually carries. QQQ and IWM stay in the price universe even though
# that dataset has no chains for them.
PRICE_SYMBOLS: tuple[str, ...] = (
    "SPY",
    "QQQ",
    "IWM",
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "META",
    "GOOGL",
    "TSLA",
    "AMD",
    "AVGO",
    "NFLX",
    "JPM",
    "AMAT",
)
OPTION_SYMBOLS: tuple[str, ...] = (
    "SPY",
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "META",
    "GOOGL",
    "TSLA",
    "AMD",
    "AVGO",
    "NFLX",
    "JPM",
    "AMAT",
)
PRICE_ONLY_SYMBOLS: tuple[str, ...] = ("QQQ", "IWM")

EQUITY0 = 100_000.0
RISK_FRAC = 0.01
MAX_ONE_LOT_RISK_FRAC = 0.025
STOCK_SLIPPAGE_BPS = 5.0
OPTION_COMMISSION = Decimal("0.65")

ATR_PERIOD = 14
ATR_STOP_MULT = 2.0
SMA_FAST = 20
SMA_MID = 50
SMA_SLOW = 200
SMA_SLOPE_LAG = 20
RSI_PERIOD = 2
MR_RSI_LONG = 10.0
MR_RSI_SHORT = 90.0
BB_WINDOW = 20
BB_MULT = 2.0
BREAKOUT_LOOKBACK = 20
BREAKOUT_VOL_MULT = 1.2
RV_WINDOW = 20
IV_PCT_WINDOW = 252
RV_MEDIAN_WINDOW = 252
IV_PERCENTILE_MIN = 0.60
TRADING_DAYS = 252

TREND_HOLD = 15
MR_HOLD = 5
BREAKOUT_HOLD = 10
PREMIUM_HOLD = 15

# target DTE, minimum DTE, maximum DTE
TREND_DTE = (35, 21, 50)
MR_DTE = (21, 14, 40)
BREAKOUT_DTE = (30, 21, 45)
PREMIUM_DTE = (35, 25, 55)

DEBIT_LONG_DELTA = Decimal("0.45")
DEBIT_DELTA_TOLERANCE = Decimal("0.15")
CREDIT_SHORT_DELTA = Decimal("0.30")
CREDIT_DELTA_TOLERANCE = Decimal("0.12")
MAX_REL_QUOTE_SPREAD = Decimal("0.20")
MAX_DEBIT_TO_WIDTH = Decimal("0.85")
MAX_CREDIT_TO_WIDTH = Decimal("0.75")
MAX_SPOT_ATM_GAP = Decimal("0.12")
EXIT_QUOTE_FORWARD_SESSIONS = 2

MIN_SAMPLE = 30
MIN_SAMPLE_NOTE = (
    "Sample is below 30 closed trades. The point estimate is descriptive only "
    "and is not evidence of a repeatable edge."
)

DOLT_SQL_URL = "https://www.dolthub.com/api/v1alpha1/post-no-preference/options/master"
CBOE_INDEX_URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/{name}_History.csv"
CBOE_EQUITY_PC_URL = "https://cdn.cboe.com/resources/options/volume_and_call_put_ratios/equitypc.csv"
CBOE_TOTAL_PC_URL = "https://cdn.cboe.com/resources/options/volume_and_call_put_ratios/totalpc.csv"
GDELT_TONE_URL = (
    "https://api.gdeltproject.org/api/v2/doc/doc"
    "?query=%22S%26P%20500%22&mode=timelinetone&format=json"
    "&startdatetime=20250601000000&enddatetime=20261111000000"
)
CNN_FEAR_GREED_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
YAHOO_CHART_URL = (
    "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    "?period1={start}&period2={end}&interval=1d&events=div%7Csplit&includeAdjustedClose=true"
)

USER_AGENT = "research-backtest/0.1 (stock-option-opp-finder; educational)"
