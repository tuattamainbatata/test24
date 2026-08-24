"""
Vishal Malkan "Grandfather-Father-Son" (GFS) RSI Range-Shift Screener -- 6-Star.

This replaces an earlier version of this file that was built on a *guessed*
"7-Star PRD" framework (trend/EMA/Supertrend + ROC + candlesticks + volume +
sector). That guess didn't hold up: deep research (elearnmarkets, Chartink,
multiple independent write-ups -- see README.md for sources) turned up no
evidence "PRD" is Malkan's term at all. What IS extensively, consistently
documented as his actual star-rated method is RSI-only, multi-timeframe:

  - 60-40 range-shift instead of the classic 70-30: in a bull regime RSI
    holds above 40; in a bear regime it's capped below 60.
  - "Grandfather / Father / Son" = Monthly / Weekly / Daily RSI(14), checked
    in a cascade: higher timeframes confirm the regime, the daily timeframe
    times the pullback entry.
  - Entry trigger: a bullish reversal candle forms right as daily RSI pulls
    back into the 40 range-shift support zone.
  - Stop: below that candle's low. Target: daily RSI back up to 60.

Six stars here (the user's own "perfect" threshold, distinct from the 5-star
and 7-star variants documented publicly -- see README.md) are the 3-timeframe
RSI regime cascade (Grandfather/Father/Son) plus three checks that turn "RSI
is in the right regime" into an actual, timed, risk-defined trade signal:
RSI already turning up off the pullback, a confirming reversal candle, and
range-shift integrity (the pullback hasn't broken down through the 40 floor).

  1. Grandfather:  Monthly RSI(14) > 60
  2. Father:       Weekly RSI(14) > 60
  3. Son:          Daily RSI(14) pulled back into range-shift support (38-50)
  4. Momentum:      Daily RSI(14) turning up (today > yesterday)
  5. Trigger:       Bullish reversal candle (hammer/engulfing/piercing) today
  6. Regime intact: Daily RSI(14) hasn't closed below 35 in the last 5 sessions

Requires: pip install -r requirements.txt
"""

import pandas as pd
try:
    import pandas_ta as ta
except ImportError:
    import pandas_ta_classic as ta  # maintained fork; same API, supports newer Python/pandas
import yfinance as yf
from tabulate import tabulate
from datetime import datetime

# ==========================================
# CONFIGURATION
# ==========================================
NSE_UNIVERSE = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS",
    "SBIN.NS", "WIPRO.NS", "ONGC.NS", "IOC.NS",
    # Full "NSE top 600, equity only" universe: load from NSE's own listing
    # (SERIES == 'EQ' already excludes ETFs/derivatives) via load_nse_universe()
    # below, ranked/truncated to 600 by market cap. This inline list is just a
    # small sample so the script runs out of the box.
]
LOOKBACK_PERIOD = "500d"  # needs 14+ monthly closes -> ~14 months minimum
MIN_SCORE_TO_REPORT = 4  # only surface stocks scoring >= this many of 6 stars
PERFECT_SCORE = 6

RSI_LENGTH = 14
GRANDFATHER_FATHER_THRESHOLD = 60  # Monthly/Weekly RSI bull-regime floor
PULLBACK_ZONE = (38, 50)  # Daily RSI range-shift support zone
REGIME_FLOOR = 35  # Daily RSI must not have closed below this in RECENT_LOOKBACK days
RECENT_LOOKBACK = 5
TARGET_RSI = 60  # documented exit: daily RSI back up to the range-shift ceiling


def load_nse_universe(csv_path, top_n=600, market_cap_col=None):
    """
    Load an NSE equity universe from a listing CSV (e.g. NSE's own
    EQUITY_L.csv: https://archives.nseindia.com/content/equity/EQUITY_L.csv).

    NSE's own equity listing already excludes ETFs and derivatives (those
    aren't in the EQ series / aren't "listed" instruments in this file), so
    no separate ETF/derivative filter is needed beyond SERIES == 'EQ'.

    If market_cap_col is given, ranks by it (descending) before truncating to
    top_n -- NSE's own listing file doesn't carry market cap, so you'll need
    to join one in yourself (FMP profile data, NSE's market cap report, etc.)
    to get a genuine "top 600 by market cap" universe. Without it, this just
    takes the first top_n rows of the file as-is.
    """
    df = pd.read_csv(csv_path)
    if "SERIES" in df.columns:
        df = df[df["SERIES"].str.strip() == "EQ"]
    if market_cap_col and market_cap_col in df.columns:
        df = df.sort_values(market_cap_col, ascending=False)
    symbols = [f"{s.strip()}.NS" for s in df["SYMBOL"].head(top_n)]
    return symbols


# ==========================================
# CORE INDICATOR CALCULATIONS
# ==========================================
def get_data(ticker, period=LOOKBACK_PERIOD, interval="1d"):
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
        if df is None or df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.columns = [str(c).lower() for c in df.columns]
        return df
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None


def calculate_indicators(df):
    """Daily-only indicators. All trailing-only (no lookahead), safe to
    precompute once over the full series."""
    df["rsi_14"] = ta.rsi(df["close"], length=RSI_LENGTH)
    df["cdl_hammer"] = ta.cdl_pattern(df["open"], df["high"], df["low"], df["close"], name="hammer")
    df["cdl_engulfing"] = ta.cdl_pattern(df["open"], df["high"], df["low"], df["close"], name="engulfing")
    df["cdl_piercing"] = ta.cdl_pattern(df["open"], df["high"], df["low"], df["close"], name="piercing")
    return df


def _mtf_rsi(df_stock, freq, length=RSI_LENGTH):
    """
    Higher-timeframe RSI, resampled fresh from whatever slice of df_stock is
    passed in (not precomputed on the full series) -- so a backtest walking
    day by day never sees a monthly/weekly bar built from future daily rows.
    """
    resampled_close = df_stock["close"].resample(freq).last()
    if len(resampled_close) < length + 1:
        return None
    rsi = ta.rsi(resampled_close, length=length)
    val = rsi.iloc[-1]
    return None if pd.isna(val) else float(val)


def check_reversal_candle(row):
    return (row["cdl_hammer"] == 100) or (row["cdl_engulfing"] == 100) or (row["cdl_piercing"] == 100)


def analyze_stock(ticker, df_stock):
    if df_stock is None or len(df_stock) < 300:  # ~14 months of trading days
        return None

    last = df_stock.iloc[-1]
    prev = df_stock.iloc[-2]
    if pd.isna(last["rsi_14"]) or pd.isna(prev["rsi_14"]):
        return None

    monthly_rsi = _mtf_rsi(df_stock, "ME")
    weekly_rsi = _mtf_rsi(df_stock, "W")
    if monthly_rsi is None or weekly_rsi is None:
        return None

    daily_rsi = float(last["rsi_14"])

    stars = {}
    stars["1_Grandfather"] = bool(monthly_rsi > GRANDFATHER_FATHER_THRESHOLD)
    stars["2_Father"] = bool(weekly_rsi > GRANDFATHER_FATHER_THRESHOLD)
    stars["3_Son"] = bool(PULLBACK_ZONE[0] <= daily_rsi <= PULLBACK_ZONE[1])
    stars["4_Momentum"] = bool(daily_rsi > float(prev["rsi_14"]))
    stars["5_Trigger"] = bool(check_reversal_candle(last))

    recent_min_rsi = df_stock["rsi_14"].tail(RECENT_LOOKBACK).min()
    stars["6_RegimeIntact"] = bool(recent_min_rsi >= REGIME_FLOOR)

    star_order = [
        ("1", "Grandfather"), ("2", "Father"), ("3", "Son"),
        ("4", "Momentum"), ("5", "Trigger"), ("6", "RegimeIntact"),
    ]
    score = sum(1 for i, k in star_order if stars[f"{i}_{k}"])

    entry = float(last["close"])
    stop_loss = float(last["low"])

    return {
        "Ticker": ticker.replace(".NS", ""),
        "ScoreNum": score,
        "Score": f"{score}/{PERFECT_SCORE}",
        "Close": round(entry, 2),
        "MonthlyRSI": round(monthly_rsi, 1),
        "WeeklyRSI": round(weekly_rsi, 1),
        "DailyRSI": round(daily_rsi, 1),
        "SL": round(stop_loss, 2),
        "TargetRule": f"Daily RSI >= {TARGET_RSI}",
        "Stars": "".join("v" if stars[f"{i}_{k}"] else "x" for i, k in star_order),
    }


# ==========================================
# MAIN EXECUTION ENGINE
# ==========================================
def run_screener(universe=None):
    universe = universe or NSE_UNIVERSE
    print(f"Scanning {len(universe)} stocks...")
    results = []

    for tk in universe:
        df = get_data(tk)
        if df is None:
            continue
        df = calculate_indicators(df)

        res = analyze_stock(tk, df)
        if res and res["ScoreNum"] >= MIN_SCORE_TO_REPORT:
            results.append(res)

    results.sort(key=lambda x: (x["ScoreNum"], x["MonthlyRSI"]), reverse=True)

    display_rows = [{k: v for k, v in r.items() if k != "ScoreNum"} for r in results]

    print("\n" + "=" * 100)
    print(f"MALKAN GFS RSI RANGE-SHIFT SCANNER (6-Star) - {datetime.now().strftime('%d-%b-%Y')}")
    print("=" * 100)
    print(tabulate(display_rows, headers="keys", tablefmt="fancy_grid", showindex=False))

    out_path = f"malkan_gfs_scan_{datetime.now().strftime('%Y%m%d')}.csv"
    pd.DataFrame(display_rows).to_csv(out_path, index=False)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    run_screener()
