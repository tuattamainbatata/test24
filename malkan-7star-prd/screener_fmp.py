"""
FMP-backed variant of the Malkan 7-Star PRD screener, for scanning NSE stocks
with your own Financial Modeling Prep API key.

Why this file exists: screener.py uses yfinance, which is free but requires
outbound internet access to Yahoo Finance. If that's unavailable to you (e.g.
a locked-down network) or you'd rather use a paid data provider, this pulls
the same OHLCV shape from FMP's REST API and runs it through the identical
7-star scoring engine (calculate_indicators / analyze_stock, imported
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
    python3 screener_fmp.py                      # default curated universe (SECTOR_MAP)
    python3 screener_fmp.py --universe nse --limit 500   # first 500 active NSE symbols
    python3 screener_fmp.py --universe nse                # ALL active NSE symbols (slow, see below)
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
    SECTOR_MAP,
    NIFTY_TICKER,
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


def get_data(symbol, lookback_days=400):
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


def fetch_nse_universe(limit=None):
    """Best-effort fetch of actively-traded NSE symbols via FMP's symbol directory."""
    data = fmp_get("company-symbols-list")
    symbols = [row["symbol"] for row in data if row.get("exchangeShortName") == "NSE" or str(row.get("symbol", "")).endswith(".NS")]
    if limit:
        symbols = symbols[:limit]
    return symbols


def run_screener(universe, min_score=MIN_SCORE_TO_REPORT):
    print(f"Fetching benchmark data ({NIFTY_TICKER})...")
    df_nifty = get_data(NIFTY_TICKER)
    df_nifty = calculate_indicators(df_nifty) if df_nifty is not None else None
    time.sleep(REQUEST_DELAY)

    sector_tickers = sorted(set(SECTOR_MAP.get(t) for t in universe if SECTOR_MAP.get(t)))
    sector_data = {}
    for st_ticker in sector_tickers:
        df_s = get_data(st_ticker)
        if df_s is not None:
            sector_data[st_ticker] = calculate_indicators(df_s)
        time.sleep(REQUEST_DELAY)

    print(f"Scanning {len(universe)} stocks (this will take a while -- one API call per symbol)...")
    results = []
    for i, tk in enumerate(universe, 1):
        df = get_data(tk)
        if df is not None:
            df = calculate_indicators(df)
            df_sector = sector_data.get(SECTOR_MAP.get(tk))
            res = analyze_stock(tk, df, df_nifty, df_sector)
            if res and res["ScoreNum"] >= min_score:
                results.append(res)
        if i % 50 == 0:
            print(f"  ...{i}/{len(universe)} scanned, {len(results)} hits so far")
        time.sleep(REQUEST_DELAY)

    results.sort(key=lambda x: (x["ScoreNum"], x["RR"]), reverse=True)
    display_rows = [{k: v for k, v in r.items() if k != "ScoreNum"} for r in results]

    print("\n" + "=" * 100)
    print(f"VISHAL MALKAN 7-STAR PRD SCANNER (FMP) - {datetime.now().strftime('%d-%b-%Y')}")
    print("=" * 100)
    print(tabulate(display_rows, headers="keys", tablefmt="fancy_grid", showindex=False))

    out_path = f"malkan_7star_scan_fmp_{datetime.now().strftime('%Y%m%d')}.csv"
    pd.DataFrame(display_rows).to_csv(out_path, index=False)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--universe", choices=["default", "nse"], default="default",
                         help="'default' = the curated SECTOR_MAP list in screener.py; "
                              "'nse' = fetch all active NSE symbols from FMP")
    parser.add_argument("--limit", type=int, default=None,
                         help="cap the number of symbols scanned (recommended with --universe nse)")
    parser.add_argument("--min-score", type=int, default=MIN_SCORE_TO_REPORT,
                         help=f"only report stocks scoring at least this many stars (default {MIN_SCORE_TO_REPORT})")
    args = parser.parse_args()

    if not API_KEY:
        sys.exit("Set FMP_API_KEY in your environment first, e.g.: export FMP_API_KEY=your_key_here")

    if args.universe == "nse":
        print("Fetching NSE symbol list from FMP...")
        stock_universe = fetch_nse_universe(limit=args.limit)
        print(f"Got {len(stock_universe)} NSE symbols.")
    else:
        stock_universe = list(SECTOR_MAP.keys())[: args.limit] if args.limit else list(SECTOR_MAP.keys())

    run_screener(stock_universe, min_score=args.min_score)
