# Google Sheets / Excel (No-Code) Implementation

Use `=GOOGLEFINANCE` (Sheets) or `=STOCKHISTORY` (Excel 365) for a data-dump sheet, then layer
the star formulas on top. RSI isn't a native sheet function, so compute it on the hidden data
sheet with the classic Wilder's-smoothing formula, or via a helper column of daily gains/losses.

| Col | Header | Formula Logic (Row 2) |
| :-- | :-- | :-- |
| A | Symbol | `RELIANCE.NS` |
| B | Close | `=GOOGLEFINANCE(A2,"price")` (daily close needs history) |
| — | Get History | `=STOCKHISTORY(A2, TODAY()-500, TODAY(), 0, 0, 1)` in Excel, or an Apps Script pulling daily OHLCV to a hidden sheet |
| C | Daily RSI(14) | Wilder's RSI on the daily close series (14-period avg gain / avg loss) |
| D | Weekly RSI(14) | RSI computed on a weekly-resampled close series (last close of each ISO week) |
| E | Monthly RSI(14) | RSI computed on a monthly-resampled close series (last close of each month) |
| F | Star 1 Grandfather | `=E2>60` |
| G | Star 2 Father | `=D2>60` |
| H | Star 3 Son | `=AND(C2>=38, C2<=50)` |
| I | Star 4 Momentum | `=C2 > OFFSET(C2,-1,0)` (today's daily RSI > yesterday's) |
| J | Star 5 Trigger | Manual check, or a nested `IF` for hammer/engulfing/piercing on Open/High/Low/Close |
| K | Star 6 Regime Intact | `=MIN(OFFSET(C2,-4,0,5,1)) >= 35` (5-session RSI low hasn't broken 35) |
| L | TOTAL SCORE | `=COUNTIF(F2:K2, TRUE)` |
| M | ACTION | `=IF(L2=6, "CORE BUY", IF(L2>=4, "WATCH", "PASS"))` |
| N | Stop | `=Low` (of the signal candle) |
| O | Target Rule | `"Exit when Daily RSI >= 60"` (RSI-level target, not a price target) |

**Pro tip:** build the data-dump sheet (daily OHLCV + resampled weekly/monthly closes) via
Python/Apps Script first. Calculating RSI natively in spreadsheet formulas across 600 stocks
will be slow and error-prone — dump the numbers, then apply the star formulas.
