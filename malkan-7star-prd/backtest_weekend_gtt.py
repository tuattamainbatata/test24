"""
Backtest of the specific real-world workflow this is meant to run as:

  1. Screen over the weekend using each week's LAST completed trading day
     (Friday, or whatever day the week actually ends on around holidays).
  2. Only stocks scoring a perfect 6/6 qualify.
  3. Place a GTT (Good-Till-Triggered) buy order on Zerodha for Monday.
  4. Entry = Monday's OPEN price (not the Friday close the signal was read
     off). Position size = floor(INR_PER_TRADE / entry_price) whole shares
     (NSE cash-market equity trades in whole shares).
  5. Exit when the stock closes more than SUPERTREND_BUFFER points below the
     daily Supertrend(10,3) value -- i.e. a GTT sell trigger at
     (Supertrend - buffer), trailing as Supertrend recalculates.

Two things worth knowing before trusting the numbers this prints:

- **This backtest treats the Supertrend trigger as auto-trailing daily.**
  Zerodha GTT orders do NOT auto-update their trigger price -- running this
  strategy for real means recalculating Supertrend and MODIFYING the GTT
  order every trading day, not "set it over the weekend and forget it."
  That's an operational commitment, not just a backtest detail.
- **The GTT trigger used for Monday's session is Friday's Supertrend value**
  (the last one known when the order would actually be placed over the
  weekend); each subsequent day's trigger is the PRIOR day's Supertrend, for
  the same reason -- you can't set a trigger today off a value you won't know
  until today's close.

Exit fill logic per day: if the open already gapped through the trigger, you
fill at the open (can't get filled above where the market opened); otherwise
if the low touched the trigger intraday, you fill at the trigger price;
otherwise the position stays open.

No separate fixed stop-loss is modeled -- Supertrend is the only exit rule,
matching what was asked for. No transaction costs, no capital-pool cap across
simultaneous positions (each ticker gets its own independent INR_PER_TRADE
budget) -- see docs/VALIDATION.md before trusting this with real money.

Usage:
    python backtest_weekend_gtt.py AAPL.csv MSFT.csv NVDA.csv --years 6
"""

import argparse
from datetime import datetime

import numpy as np
import pandas as pd
from tabulate import tabulate

from screener import calculate_indicators, analyze_stock, PERFECT_SCORE

INR_PER_TRADE = 60000
SUPERTREND_BUFFER = 1  # points below Supertrend before the GTT triggers


def load_csv(path):
    df = pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()
    return df[["open", "high", "low", "close", "volume"]]


def week_end_dates(index):
    """Last available trading day of each calendar week in the index."""
    s = pd.Series(index, index=index)
    return s.groupby(index.to_period("W")).last().tolist()


def simulate_trades(ticker, df, warmup=300):
    trades = []
    positions_locked_until = None  # date index label; None = flat

    week_ends = week_end_dates(df.index)
    idx_of = {d: i for i, d in enumerate(df.index)}

    for wi, friday in enumerate(week_ends):
        f_pos = idx_of[friday]
        if f_pos < warmup:
            continue
        if positions_locked_until is not None and friday <= positions_locked_until:
            continue  # still in a position opened on/before this week

        window = df.iloc[: f_pos + 1]
        res = analyze_stock(ticker, window)
        if res is None or res["ScoreNum"] != PERFECT_SCORE:
            continue

        entry_pos = f_pos + 1
        if entry_pos >= len(df):
            continue  # signal on the last available Friday, no Monday to enter on

        entry_date = df.index[entry_pos]
        entry_price = float(df["open"].iloc[entry_pos])
        shares = int(INR_PER_TRADE // entry_price)
        if shares <= 0:
            continue  # entry price exceeds the per-trade budget

        # trigger for session j is the PRIOR session's Supertrend value, since
        # that's the last value known when the GTT order would be (re)placed
        trigger_for = lambda j: float(df["st_value"].iloc[j - 1]) - SUPERTREND_BUFFER

        exit_price = exit_date = None
        j = entry_pos
        while j < len(df):
            trig = trigger_for(j)
            if pd.isna(trig):
                j += 1
                continue
            day_open = float(df["open"].iloc[j])
            day_low = float(df["low"].iloc[j])
            if day_open <= trig:
                exit_price, exit_date = day_open, df.index[j]
            elif day_low <= trig:
                exit_price, exit_date = trig, df.index[j]
            if exit_price is not None:
                break
            j += 1

        if exit_price is None:  # still open at the end of the data
            exit_price, exit_date = float(df["close"].iloc[-1]), df.index[-1]
            j = len(df) - 1

        invested = shares * entry_price
        pnl_cash = shares * (exit_price - entry_price)
        trades.append({
            "Ticker": ticker,
            "SignalFriday": friday.date(),
            "EntryDate": entry_date.date(),
            "EntryOpen": round(entry_price, 2),
            "Shares": shares,
            "Invested": round(invested, 2),
            "ExitDate": exit_date.date(),
            "ExitPrice": round(exit_price, 2),
            "HoldDays": (exit_date - entry_date).days,
            "PnL": round(pnl_cash, 2),
            "PnL%": round((exit_price - entry_price) / entry_price * 100, 2),
        })
        positions_locked_until = exit_date

    return trades


def summarize(trades):
    if not trades:
        return {"trades": 0}
    pnl = np.array([t["PnL"] for t in trades])
    pnl_pct = np.array([t["PnL%"] for t in trades])
    invested = np.array([t["Invested"] for t in trades])
    wins = pnl > 0
    equity = np.cumsum(pnl)
    running_max = np.maximum.accumulate(equity)
    max_dd = float(np.min(equity - running_max)) if len(equity) else 0.0
    return {
        "trades": len(trades),
        "win_rate_pct": round(100 * wins.sum() / len(pnl), 1),
        "total_invested": round(float(invested.sum()), 2),
        "total_pnl_inr": round(float(pnl.sum()), 2),
        "avg_pnl_pct": round(float(pnl_pct.mean()), 2),
        "avg_win_pct": round(float(pnl_pct[wins].mean()), 2) if wins.any() else 0.0,
        "avg_loss_pct": round(float(pnl_pct[~wins].mean()), 2) if (~wins).any() else 0.0,
        "max_drawdown_inr": round(max_dd, 2),
        "avg_hold_days": round(float(np.mean([t["HoldDays"] for t in trades])), 1),
    }


def run(tickers_csv, years):
    all_trades = []
    for path in tickers_csv:
        ticker = path.split("/")[-1].replace(".csv", "")
        df = calculate_indicators(load_csv(path))  # full history -- indicators need the runway

        warmup_rows = 300  # ~14 months, enough for monthly RSI to warm up
        if years:
            cutoff = df.index.max() - pd.DateOffset(years=years)
            warmup_rows = max(warmup_rows, int((df.index < cutoff).sum()))

        trades = simulate_trades(ticker, df, warmup=warmup_rows)
        all_trades.extend(trades)
        print(f"{ticker}: {len(trades)} trades")

    print("\n" + "=" * 100)
    print(f"WEEKEND SCAN -> MONDAY OPEN -> INR {INR_PER_TRADE} -> SUPERTREND EXIT (6/6 only)")
    print("=" * 100)
    if all_trades:
        print(tabulate(all_trades, headers="keys", tablefmt="fancy_grid", showindex=False))
    stats = summarize(all_trades)
    print("\n--- Summary ---")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    out = f"backtest_weekend_gtt_{datetime.now().strftime('%Y%m%d')}.csv"
    pd.DataFrame(all_trades).to_csv(out, index=False)
    print(f"\nTrade log saved to {out}")
    return all_trades, stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("tickers", nargs="+", help="CSV files (date,open,high,low,close,volume) to backtest")
    parser.add_argument("--years", type=int, default=6, help="only score/trade within the last N years (default 6)")
    args = parser.parse_args()

    run(args.tickers, args.years)
