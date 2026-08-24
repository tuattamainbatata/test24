# Vishal Malkan "7-Star PRD" Stock Screening Framework

> **Disclaimer:** Vishal Malkan (Malkansview) teaches proprietary setups. "PRD" in his
> terminology typically refers to **"Price Rate of Change" (ROC) Momentum** combined with a
> **"Pullback Reversal Day"** candle pattern. The "7-Star" is a confluence checklist. The logic
> below reverse-engineers his public webinars/teachings (Supertrend, ROC, Volume, Price Action,
> Structure) into a codifiable, quantitative framework. This is not financial advice — validate
> with your own backtests before trading real capital.

## The 7-Star Confluence Checklist

| Star # | Malkan Concept | Quantitative Rule (Default Params) |
| :--- | :--- | :--- |
| ⭐ 1 | Trend Alignment | Price > 50 EMA > 200 EMA (Daily). Supertrend (10, 3) = Green. |
| ⭐ 2 | PRD Momentum (ROC) | ROC(9) > 0 AND ROC(9) > ROC(9)[1] (Accelerating Momentum). |
| ⭐ 3 | Pullback & Reversal (PRD Candle) | Bullish Reversal Candle (Hammer/Bullish Engulfing/Piercing) at Key Support (50 EMA / Supertrend). |
| ⭐ 4 | Volume Confirmation | Volume > 1.5x 20-Day Avg Volume on the Reversal Candle (Star 3). |
| ⭐ 5 | Relative Strength (RS) | Stock ROC(20) > Nifty 50 ROC(20) (Outperforming Benchmark). |
| ⭐ 6 | Risk:Reward Structure | Target (Swing High) / Stop Loss (Reversal Candle Low) >= 2.5:1. |
| ⭐ 7 | Sector Tailwind | Sector Index > 50 EMA AND Sector ROC(9) > 0. |

**Scoring:** 7/7 = "Core Buy" · 6/7 = "Watchlist" · <6 = Ignore.

## Contents

- `screener.py` — production-ready Python scanner (yfinance + pandas_ta).
- `screener_fmp.py` — same scoring engine, backed by Financial Modeling Prep's REST API instead
  of yfinance. Use this if yfinance is blocked on your network, or if you'd rather use a paid
  data provider. **Requires an FMP plan with international/NSE exchange access** (their free
  tier only covers US exchanges) — get a key at financialmodelingprep.com.
- `backtest.py` — walk-forward backtester: reuses `calculate_indicators`/`analyze_stock`
  unchanged, simulates entries at the signal-day close with the framework's own stop
  (candle low) and target (20-day swing high), and reports win rate, R-multiples,
  expectancy, and profit factor by score tier.
- `pinescript/malkan_7star_prd.pine` — TradingView Pine Script v5 indicator with dashboard + alerts.
- `sheets/FORMULAS.md` — Google Sheets / Excel no-code formula reference.
- `docs/ARCHITECTURE.md` — deployment architecture (scheduler → scan → alert pipeline).
- `docs/VALIDATION.md` — backtest / validation checklist before going live.

## Quick Start (Python, yfinance)

```bash
cd malkan-7star-prd
pip install -r requirements.txt
python screener.py
```

Edit the `SECTOR_MAP` dict in `screener.py` to define your stock universe and each stock's
sector benchmark index. Results with score >= 5/7 print to console and save to a CSV.

## Quick Start (Python, FMP)

```bash
cd malkan-7star-prd
pip install -r requirements.txt
export FMP_API_KEY=your_key_here
python screener_fmp.py --universe default        # curated SECTOR_MAP list
python screener_fmp.py --universe nse --limit 500  # first 500 active NSE symbols from FMP
python screener_fmp.py --universe nse               # every active NSE symbol (slow — one API
                                                      # call per symbol, ~2000+ symbols; consider
                                                      # capping with --limit or scanning a curated
                                                      # list like Nifty 500 instead of the full tape)
```

`screener_fmp.py` hasn't been run against live FMP responses (this repo was built in an
environment with no route to financialmodelingprep.com) — sanity-check it against a couple of
known tickers before pointing it at the whole exchange, and adjust `get_data()` /
`fetch_nse_universe()` if FMP's field names have moved since this was written.

## Backtesting

```bash
cd malkan-7star-prd
python backtest.py AAPL.csv MSFT.csv NVDA.csv --benchmark SPY.csv --min-score 7 --max-hold 60
```

Each CSV needs `date,open,high,low,close,volume` columns — export these from `screener.py`'s
data source (yfinance/FMP), your broker, or NSE's own historical archives. See `docs/VALIDATION.md`
for the full pre-live checklist (slippage, sector-correlation caps, regime filters) — a
backtest with no transaction costs and no sector diversification will overstate the edge.

A real run against AAPL/MSFT/NVDA (2021–2026, SPY as benchmark, no sector data available) found:
7/7 signals never fired in ~1,400 trading days per name; 6/7 fired 9 times with a negative
expectancy (small sample); 5/7 fired 143 times with positive expectancy (+0.79R, profit factor
2.15) but almost all of that edge came from 2 of the 3 tickers. Small-N, non-NSE, no-cost caveats
apply in full — see the framework's own validation checklist before trusting any of that.

## Key "Malkan Nuances" Encoded in This Implementation

1. **PRD = ROC Acceleration**, not just `ROC > 0`. It must be *rising* (`ROC[0] > ROC[1]`) to
   catch the start of momentum, not a stalling move.
2. **Candle Context (Star 3):** A hammer at the 50 EMA in a downtrend is a trap — Star 1
   (trend up) and Star 3 (reversal candle at support) are scored independently but both must be
   true for a valid "Core Buy".
3. **Volume on the reversal candle** (Star 4), not the breakout candle — confirms accumulation
   on the dip rather than late chasing.
4. **Sector Filter (Star 7):** "A rising tide lifts all boats." If the sector is weak, treat a
   7/7 signal as lower-conviction (e.g. halve position size) even though it technically scores.
5. **Exit strategy** (not scored, but part of the system): trail stop with Supertrend(10,3)
   flip to red; take partial profit at 1:1 R:R and trail the rest.
