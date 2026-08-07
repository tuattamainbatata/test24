# Google Sheets / Excel (No-Code) Implementation

Use `=GOOGLEFINANCE` (Sheets) or `=STOCKHISTORY` (Excel 365) plus helper columns. Calculating
Supertrend and ROC across 200+ stocks natively in spreadsheet formulas is slow and error-prone —
**build a "data dump" sheet via the Python screener or an Apps Script first**, then layer the
star formulas on top of that data.

| Col | Header | Formula Logic (Row 2) |
| :-- | :-- | :-- |
| A | Symbol | `RELIANCE.NS` |
| B | Close | `=GOOGLEFINANCE(A2,"price")` (daily close needs history) |
| — | Get History | `=STOCKHISTORY(A2, TODAY()-400, TODAY(), 0, 0, 1)` in Excel, or an Apps Script pulling OHLCV to a hidden sheet |
| C | EMA 50 | `=AVERAGE(OFFSET(Close_Range, -50, 0, 50))` (on the hidden data sheet) |
| D | EMA 200 | `=AVERAGE(OFFSET(Close_Range, -200, 0, 200))` |
| E | Supertrend | Complex in sheets — compute in Python/TradingView and paste in, or approximate: `=IF(Close > UpperBand, "Green", "Red")` |
| F | ROC(9) | `=(Close - OFFSET(Close, -9, 0)) / OFFSET(Close, -9, 0) * 100` |
| G | ROC Prev | `=OFFSET(F2, -1, 0)` |
| H | Star 1 Trend | `=AND(B2>C2, C2>D2, E2="Green")` |
| I | Star 2 PRD | `=AND(F2>0, F2>G2)` |
| J | Star 3 Candle | Manual check, or a nested `IF(AND(Close>Open, (High-Close)<(Close-Open)*0.5, (Open-Low)>(Close-Open)*2), "Hammer", IF(...))` |
| K | Star 4 Vol | `=Volume > 1.5 * AVERAGE(Vol_Range_Last_20)` |
| L | Star 5 RS | `=F2 > Nifty_ROC_20` (pull Nifty ROC separately) |
| M | Star 6 RR | `=(Target_20High - Close) / (Close - Low_Candle) >= 2.5` |
| N | Star 7 Sector | `=AND(Sector_Close > Sector_EMA50, Sector_ROC9 > 0)` |
| O | TOTAL SCORE | `=COUNTIF(H2:N2, TRUE)` |
| P | ACTION | `=IF(O2=7, "CORE BUY", IF(O2=6, "WATCH", "PASS"))` |

**Pro tip:** the data-dump sheet only needs to be refreshed once per day (or once per session) —
schedule an Apps Script trigger (Sheets > Extensions > Apps Script > Triggers) for `09:15 IST` and
`15:30 IST` to keep it current without manual refreshes.
