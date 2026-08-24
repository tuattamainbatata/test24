"""
Walk-forward backtester for the Malkan GFS RSI Range-Shift framework (6-Star).

Reuses calculate_indicators() / analyze_stock() from screener.py unchanged.
The daily RSI and candle-pattern columns calculate_indicators() adds are
trailing-only, so they're safe to precompute once over the full series; the
monthly/weekly RSI (Grandfather/Father) are recomputed by analyze_stock()
itself from whatever slice it's given, which is what keeps this lookahead-free
-- walking forward by slicing df.iloc[:t+1] means iloc[-1] of that slice is
exactly "what was knowable at the close of day t", and the monthly/weekly RSI
built from that slice never sees a future daily row.

Trade simulation rules (see docs/VALIDATION.md for why these matter):
  - Signal fires on day t if score >= min_score AND no open position in that
    name. Entry = day t's close (the same close the signal was computed from
    -- a common backtest simplification; real execution would be next day's
    open plus slippage).
  - Stop = day t's low (the signal candle's own low, per the documented rule).
  - Target: exit when daily RSI(14) closes back at/above TARGET_RSI (60) --
    the documented target is an RSI level, not a price level.
  - Priority each subsequent day: stop hit (low <= stop) > RSI target hit >
    max holding period.
  - One position per ticker at a time; scanning resumes the day after exit.

Usage:
    python backtest.py AAPL.csv MSFT.csv NVDA.csv --min-score 6
    python backtest.py AAPL.csv --min-score 4 --max-hold 60

Each positional CSV must have columns: date,open,high,low,close,volume.
"""

import argparse
from datetime import datetime

import numpy as np
import pandas as pd
from tabulate import tabulate

from screener import calculate_indicators, analyze_stock, TARGET_RSI, MIN_SCORE_TO_REPORT, PERFECT_SCORE


def load_csv(path):
    df = pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()
    return df[["open", "high", "low", "close", "volume"]]


def simulate_trades(ticker, df, min_score, max_hold_days, warmup=300):
    trades = []
    i = warmup
    n = len(df)
    while i < n - 1:  # need at least one future bar to exit on
        window = df.iloc[: i + 1]

        res = analyze_stock(ticker, window)
        if res is None or res["ScoreNum"] < min_score:
            i += 1
            continue

        entry_date = df.index[i]
        entry_price = float(df["close"].iloc[i])
        stop = float(df["low"].iloc[i])
        risk = entry_price - stop
        if risk <= 0:
            i += 1
            continue

        exit_price = exit_date = exit_reason = None
        j = i + 1
        hold_limit = min(n - 1, i + max_hold_days)
        while j <= hold_limit:
            day = df.iloc[j]
            if day["low"] <= stop:
                exit_price, exit_reason = stop, "stop"
            elif day["rsi_14"] >= TARGET_RSI:
                exit_price, exit_reason = float(day["close"]), "target (RSI)"
            elif j == hold_limit:
                exit_price, exit_reason = float(day["close"]), "time"
            if exit_price is not None:
                exit_date = df.index[j]
                break
            j += 1

        if exit_price is None:  # ran off the end of data still in the trade
            exit_price, exit_date, exit_reason = float(df["close"].iloc[-1]), df.index[-1], "data ended"
            j = n - 1

        trades.append({
            "Ticker": ticker,
            "Score": res["Score"],
            "EntryDate": entry_date.date(),
            "Entry": round(entry_price, 2),
            "Stop": round(stop, 2),
            "ExitDate": exit_date.date(),
            "Exit": round(exit_price, 2),
            "Reason": exit_reason,
            "HoldDays": (exit_date - entry_date).days,
            "PnL%": round((exit_price - entry_price) / entry_price * 100, 2),
            "R": round((exit_price - entry_price) / risk, 2),
        })
        i = j + 1  # resume scanning the day after exit

    return trades


def summarize(trades):
    if not trades:
        return {"trades": 0}
    r = np.array([t["R"] for t in trades])
    wins = r[r > 0]
    losses = r[r <= 0]
    equity = np.cumsum(r)
    running_max = np.maximum.accumulate(equity)
    max_dd = float(np.min(equity - running_max)) if len(equity) else 0.0
    reasons = {}
    for t in trades:
        reasons[t["Reason"]] = reasons.get(t["Reason"], 0) + 1
    return {
        "trades": len(trades),
        "win_rate_pct": round(100 * len(wins) / len(r), 1),
        "avg_R": round(float(r.mean()), 2),
        "avg_win_R": round(float(wins.mean()), 2) if len(wins) else 0.0,
        "avg_loss_R": round(float(losses.mean()), 2) if len(losses) else 0.0,
        "profit_factor": round(float(wins.sum() / abs(losses.sum())), 2) if losses.sum() != 0 else float("inf"),
        "expectancy_R": round(float(r.mean()), 2),
        "total_R": round(float(r.sum()), 2),
        "max_drawdown_R": round(max_dd, 2),
        "avg_hold_days": round(float(np.mean([t["HoldDays"] for t in trades])), 1),
        "exit_reasons": reasons,
    }


def run(tickers_csv, min_score, max_hold_days):
    all_trades = []
    for path in tickers_csv:
        ticker = path.split("/")[-1].replace(".csv", "")
        df = calculate_indicators(load_csv(path))
        trades = simulate_trades(ticker, df, min_score, max_hold_days)
        all_trades.extend(trades)
        print(f"{ticker}: {len(trades)} trades")

    print("\n" + "=" * 100)
    print(f"MALKAN GFS RSI BACKTEST -- min_score={min_score}/{PERFECT_SCORE}, max_hold={max_hold_days}d")
    print("=" * 100)
    if all_trades:
        print(tabulate(all_trades, headers="keys", tablefmt="fancy_grid", showindex=False))
    stats = summarize(all_trades)
    print("\n--- Summary ---")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    out = f"backtest_trades_{datetime.now().strftime('%Y%m%d')}.csv"
    pd.DataFrame(all_trades).to_csv(out, index=False)
    print(f"\nTrade log saved to {out}")
    return all_trades, stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("tickers", nargs="+", help="CSV files (date,open,high,low,close,volume) to backtest")
    parser.add_argument("--min-score", type=int, default=MIN_SCORE_TO_REPORT,
                         help=f"minimum star score to enter (default {MIN_SCORE_TO_REPORT}/{PERFECT_SCORE})")
    parser.add_argument("--max-hold", type=int, default=60, help="max holding period in trading days (default 60)")
    args = parser.parse_args()

    run(args.tickers, args.min_score, args.max_hold)
