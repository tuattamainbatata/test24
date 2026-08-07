"""
Vishal Malkan "7-Star PRD" Stock Screening Framework.

Screens a stock universe against the 7-star confluence checklist:
  1. Trend Alignment (Price > 50 EMA > 200 EMA, Supertrend green)
  2. PRD Momentum (ROC(9) positive and accelerating)
  3. Pullback & Reversal Candle at support (hammer / engulfing / piercing)
  4. Volume confirmation (>1.5x 20-day avg on the reversal candle)
  5. Relative strength vs Nifty 50 (ROC(20) stock > ROC(20) index)
  6. Risk:Reward >= 2.5 (swing-high target vs reversal-candle-low stop)
  7. Sector tailwind (sector index > 50 EMA and ROC(9) > 0)

Requires: pip install -r requirements.txt
"""

import pandas as pd
import pandas_ta as ta
import yfinance as yf
from tabulate import tabulate
from datetime import datetime

# ==========================================
# CONFIGURATION
# ==========================================
NIFTY_TICKER = "^NSEI"
SECTOR_MAP = {
    "RELIANCE.NS": "^CNXENERGY", "ONGC.NS": "^CNXENERGY", "IOC.NS": "^CNXENERGY",
    "HDFCBANK.NS": "^CNXBANK", "ICICIBANK.NS": "^CNXBANK", "SBIN.NS": "^CNXBANK",
    "TCS.NS": "^CNXIT", "INFY.NS": "^CNXIT", "WIPRO.NS": "^CNXIT",
    # ADD YOUR UNIVERSE MAPPING HERE (stock -> sector benchmark index)
}
UNIVERSE = list(SECTOR_MAP.keys())  # Or load from an NSE 200/500 CSV
LOOKBACK_PERIOD = "400d"  # Enough history for a 200 EMA to warm up
MIN_SCORE_TO_REPORT = 5  # Only surface stocks scoring >= this many stars


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
    # Trend
    df["ema_50"] = ta.ema(df["close"], length=50)
    df["ema_200"] = ta.ema(df["close"], length=200)

    # Supertrend (10, 3)
    st = ta.supertrend(df["high"], df["low"], df["close"], length=10, multiplier=3)
    df = pd.concat([df, st], axis=1)
    dir_col = next(c for c in st.columns if c.startswith("SUPERTd_"))
    val_col = next(c for c in st.columns if c.startswith("SUPERT_") and not c.startswith(("SUPERTd_", "SUPERTl_", "SUPERTs_")))
    # pandas_ta convention: -1 = uptrend (green), 1 = downtrend (red)
    df["st_dir"] = df[dir_col]
    df["st_value"] = df[val_col]

    # ROC (Rate of Change) - PRD core
    df["roc_9"] = ta.roc(df["close"], length=9)
    df["roc_20"] = ta.roc(df["close"], length=20)

    # Volume
    df["vol_avg_20"] = ta.sma(df["volume"], length=20)

    # Candlestick patterns (PRD reversal). 100 = bullish, -100 = bearish, 0 = none.
    df["cdl_hammer"] = ta.cdl_pattern(df["open"], df["high"], df["low"], df["close"], name="hammer")
    df["cdl_engulfing"] = ta.cdl_pattern(df["open"], df["high"], df["low"], df["close"], name="engulfing")
    df["cdl_piercing"] = ta.cdl_pattern(df["open"], df["high"], df["low"], df["close"], name="piercing")

    # Swing high/low for R:R
    df["swing_high_20"] = df["high"].rolling(20).max()

    return df


def check_reversal_candle(row):
    """Star 3: Bullish reversal pattern occurring at a key support zone."""
    is_pattern = (row["cdl_hammer"] == 100) or (row["cdl_engulfing"] == 100) or (row["cdl_piercing"] == 100)
    if not is_pattern:
        return False

    price = row["close"]
    near_50 = abs(price - row["ema_50"]) / price < 0.015
    near_st = abs(price - row["st_value"]) / price < 0.015
    return near_50 or near_st


def analyze_stock(ticker, df_stock, df_nifty, df_sector):
    if df_stock is None or len(df_stock) < 210:
        return None

    last = df_stock.iloc[-1]
    prev = df_stock.iloc[-2]
    nifty_last = df_nifty.iloc[-1] if df_nifty is not None else None
    sector_last = df_sector.iloc[-1] if df_sector is not None else None

    stars = {}

    # Star 1: Trend Alignment
    trend_up = (last["close"] > last["ema_50"]) and (last["ema_50"] > last["ema_200"])
    st_green = last["st_dir"] == -1
    stars["1_Trend"] = bool(trend_up and st_green)

    # Star 2: PRD Momentum (ROC acceleration)
    roc_pos = last["roc_9"] > 0
    roc_accel = last["roc_9"] > prev["roc_9"]
    stars["2_PRDMomentum"] = bool(roc_pos and roc_accel)

    # Star 3: PRD reversal candle at support (today)
    stars["3_ReversalCandle"] = bool(check_reversal_candle(last))

    # Star 4: Volume surge on the reversal candle
    stars["4_Volume"] = bool(last["volume"] > (1.5 * last["vol_avg_20"]))

    # Star 5: Relative strength vs Nifty
    nifty_roc_20 = nifty_last["roc_20"] if nifty_last is not None else 0
    stars["5_RelStrength"] = bool(last["roc_20"] > nifty_roc_20)

    # Star 6: Risk:Reward >= 2.5
    entry = last["close"]
    stop_loss = last["low"]  # Low of the reversal candle
    target = last["swing_high_20"]  # Nearest resistance

    if entry > stop_loss and target > entry:
        rr = (target - entry) / (entry - stop_loss)
        stars["6_RiskReward"] = bool(rr >= 2.5)
        rr_value = round(rr, 2)
    else:
        stars["6_RiskReward"] = False
        rr_value = 0

    # Star 7: Sector tailwind
    if sector_last is not None:
        sec_trend = sector_last["close"] > sector_last["ema_50"]
        sec_mom = sector_last["roc_9"] > 0
        stars["7_Sector"] = bool(sec_trend and sec_mom)
    else:
        stars["7_Sector"] = True  # Neutral if no sector data supplied

    star_order = [
        ("1", "Trend"), ("2", "PRDMomentum"), ("3", "ReversalCandle"),
        ("4", "Volume"), ("5", "RelStrength"), ("6", "RiskReward"), ("7", "Sector"),
    ]
    score = sum(1 for i, k in star_order if stars[f"{i}_{k}"])

    return {
        "Ticker": ticker.replace(".NS", ""),
        "ScoreNum": score,
        "Score": f"{score}/7",
        "Close": round(entry, 2),
        "ROC(9)": round(last["roc_9"], 2),
        "RR": rr_value,
        "SL": round(stop_loss, 2),
        "Target": round(target, 2),
        "Stars": "".join("v" if stars[f"{i}_{k}"] else "x" for i, k in star_order),
    }


# ==========================================
# MAIN EXECUTION ENGINE
# ==========================================
def run_screener():
    print(f"Fetching benchmark data ({NIFTY_TICKER})...")
    df_nifty = get_data(NIFTY_TICKER)
    if df_nifty is not None:
        df_nifty = calculate_indicators(df_nifty)

    sector_tickers = sorted(set(SECTOR_MAP.values()))
    sector_data = {}
    for st_ticker in sector_tickers:
        df_s = get_data(st_ticker)
        if df_s is not None:
            sector_data[st_ticker] = calculate_indicators(df_s)

    print(f"Scanning {len(UNIVERSE)} stocks...")
    results = []

    for tk in UNIVERSE:
        df = get_data(tk)
        if df is None:
            continue
        df = calculate_indicators(df)

        sector_tk = SECTOR_MAP.get(tk)
        df_sector = sector_data.get(sector_tk)

        res = analyze_stock(tk, df, df_nifty, df_sector)
        if res and res["ScoreNum"] >= MIN_SCORE_TO_REPORT:
            results.append(res)

    results.sort(key=lambda x: (x["ScoreNum"], x["RR"]), reverse=True)

    display_rows = [{k: v for k, v in r.items() if k != "ScoreNum"} for r in results]

    print("\n" + "=" * 100)
    print(f"VISHAL MALKAN 7-STAR PRD SCANNER RESULTS - {datetime.now().strftime('%d-%b-%Y')}")
    print("=" * 100)
    print(tabulate(display_rows, headers="keys", tablefmt="fancy_grid", showindex=False))

    out_path = f"malkan_7star_scan_{datetime.now().strftime('%Y%m%d')}.csv"
    pd.DataFrame(display_rows).to_csv(out_path, index=False)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    run_screener()
