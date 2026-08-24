"""
FMP-backed variant of the Malkan GFS RSI Range-Shift screener, for scanning
NSE stocks with your own Financial Modeling Prep API key.

Why this file exists: screener.py uses yfinance, which is free but requires
outbound internet access to Yahoo Finance. If that's unavailable to you (e.g.
a locked-down network) or you'd rather use a paid data provider, this pulls
the same OHLCV shape from FMP's REST API and runs it through the identical
6-star scoring engine (calculate_indicators / analyze_stock, imported
unchanged from screener.py).

Requires a paid FMP plan (Starter or higher) -- FMP's free tier only serves
US-exchange data, not NSE/BSE. Get a key at https://financialmodelingprep.com

NOTE: this has not been run against live FMP responses (this dev environment
has no route to financialmodelingprep.com). The endpoint paths below match
FMP's documented "stable" API as of writing; if FMP has changed field names
since, adjust get_data()/fetch_nse_universe() to match what you actually get
back -- run with a couple of known tickers first (e.g. RELIANCE.NS) before
pointing it at the full exchange.

Usage:
    export FMP_API_KEY=your_key_here
    pip install -r requirements.txt requests
    python3 screener_fmp.py                           # small sample universe (NSE_UNIVERSE)
    python3 screener_fmp.py --universe nse --limit 600  # top 600 active NSE equities from FMP
    python3 screener_fmp.py --universe nse               # ALL active NSE equities (slow, see below)
"""

import argparse
import os
import sys
import time
from datetime import datetime, timedelta

import pandas as pd
import requests
from tabulate import tabulate

from screener import (
    NSE_UNIVERSE,
    MIN_SCORE_TO_REPORT,
    calculate_indicators,
    analyze_stock,
)

FMP_BASE = "https://financialmodelingprep.com/stable"
API_KEY = os.environ.get("FMP_API_KEY")
REQUEST_DELAY = 0.25  # seconds between calls -- stay polite / under rate limits


def fmp_get(path, **params):
    if not API_KEY:
        raise RuntimeError("Set the FMP_API_KEY environment variable first.")
    params["apikey"] = API_KEY
    resp = requests.get(f"{FMP_BASE}/{path}", params=params, timeout=20)
    resp.raise_for_status()
    return resp.json()


def get_data(symbol, lookback_days=500):
    to_date = datetime.now().date()
    from_date = to_date - timedelta(days=int(lookback_days * 1.6))  # pad for weekends/holidays
    try:
        data = fmp_get(
            "historical-price-eod/full",
            symbol=symbol,
            **{"from": from_date.isoformat(), "to": to_date.isoformat()},
        )
    except requests.HTTPError as e:
        print(f"Error fetching {symbol}: {e}")
        return None
    if not data:
        return None
    df = pd.DataFrame(data)
    if df.empty or "close" not in df.columns:
        return None
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").set_index("date")
    return df[["open", "high", "low", "close", "volume"]]


def fetch_nse_universe(limit=600):
    """
    Best-effort fetch of active NSE equity symbols via FMP's symbol directory,
    excluding ETFs/funds. FMP's company-symbols-list doesn't reliably flag
    ETFs per-exchange, so this filters on isEtf/isFund when present and drops
    obvious fund-name patterns as a fallback -- spot-check the result before
    trusting it, this hasn't been run against a live response.
    """
    data = fmp_get("company-symbols-list")
    symbols = []
    for row in data:
        sym = str(row.get("symbol", ""))
        if not (row.get("exchangeShortName") == "NSE" or sym.endswith(".NS")):
            continue
        if row.get("isEtf") or row.get("isFund"):
            continue
        name = str(row.get("name", "")).lower()
        if "etf" in name or " fund" in name:
            continue
        symbols.append(sym)
    if limit:
        symbols = symbols[:limit]
    return symbols


def run_screener(universe, min_score=MIN_SCORE_TO_REPORT):
    print(f"Scanning {len(universe)} stocks (this will take a while -- one API call per symbol)...")
    results = []
    for i, tk in enumerate(universe, 1):
        df = get_data(tk)
        if df is not None:
            df = calculate_indicators(df)
            res = analyze_stock(tk, df)
            if res and res["ScoreNum"] >= min_score:
                results.append(res)
        if i % 50 == 0:
            print(f"  ...{i}/{len(universe)} scanned, {len(results)} hits so far")
        time.sleep(REQUEST_DELAY)

    results.sort(key=lambda x: (x["ScoreNum"], x["MonthlyRSI"]), reverse=True)
    display_rows = [{k: v for k, v in r.items() if k != "ScoreNum"} for r in results]

    print("\n" + "=" * 100)
    print(f"MALKAN GFS RSI RANGE-SHIFT SCANNER (FMP, 6-Star) - {datetime.now().strftime('%d-%b-%Y')}")
    print("=" * 100)
    print(tabulate(display_rows, headers="keys", tablefmt="fancy_grid", showindex=False))

    out_path = f"malkan_gfs_scan_fmp_{datetime.now().strftime('%Y%m%d')}.csv"
    pd.DataFrame(display_rows).to_csv(out_path, index=False)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--universe", choices=["default", "nse"], default="default",
                         help="'default' = the small sample list in screener.py; "
                              "'nse' = fetch active NSE equity symbols from FMP")
    parser.add_argument("--limit", type=int, default=600,
                         help="cap the number of symbols scanned (default 600, matching 'top 600')")
    parser.add_argument("--min-score", type=int, default=MIN_SCORE_TO_REPORT,
                         help=f"only report stocks scoring at least this many of 6 stars (default {MIN_SCORE_TO_REPORT})")
    args = parser.parse_args()

    if not API_KEY:
        sys.exit("Set FMP_API_KEY in your environment first, e.g.: export FMP_API_KEY=your_key_here")

    if args.universe == "nse":
        print("Fetching NSE equity symbol list from FMP...")
        stock_universe = fetch_nse_universe(limit=args.limit)
        print(f"Got {len(stock_universe)} NSE symbols.")
    else:
        stock_universe = NSE_UNIVERSE[: args.limit] if args.limit else NSE_UNIVERSE

    run_screener(stock_universe, min_score=args.min_score)
