# Vishal Malkan "Grandfather-Father-Son" RSI Range-Shift Screener (6-Star)

> **Correction from an earlier version of this project:** this was originally built around a
> "7-Star PRD" framework (trend/EMA/Supertrend + ROC momentum + candlestick patterns + volume +
> sector rotation) that turned out to be **speculative** — deep research found no evidence
> Malkan uses the term "PRD" at all. What's actually extensively and consistently documented as
> his real star-rated method is completely different: **RSI-only, multi-timeframe.** This
> version replaces the old framework entirely. See "Research sources" below.

## The real framework: RSI Range-Shift + Grandfather-Father-Son

- **60-40 range-shift**, not the classic 70-30: in a bull regime RSI holds above 40; in a bear
  regime it's capped below 60.
- **"Grandfather / Father / Son"** = Monthly / Weekly / Daily RSI(14), checked as a cascade:
  higher timeframes confirm the regime, the daily timeframe times the pullback entry.
- **Entry trigger**: a bullish reversal candle forms right as daily RSI pulls back into the 40
  range-shift support zone.
- **Stop**: below that candle's low. **Target**: daily RSI back up to 60.

Public sources describe 5-star and 7-star variants of this system (more timeframes = more
stars — the 7-star Chartink version adds Hourly and 15-min on top of Monthly/Weekly/Daily).
Neither is independently documented as a "6-star" version, and Malkan's exact proprietary
criteria per star-count isn't public. This implementation is a considered 6-star adaptation for
an **end-of-day (daily close) screener** — no intraday timeframes — built from the same
mechanics: the 3-timeframe RSI cascade, plus three checks that turn "RSI is in the right regime"
into an actual, timed, risk-defined trade signal.

## The 6-Star Checklist

| Star # | Name | Rule |
| :--- | :--- | :--- |
| ⭐ 1 | Grandfather | Monthly RSI(14) > 60 |
| ⭐ 2 | Father | Weekly RSI(14) > 60 |
| ⭐ 3 | Son | Daily RSI(14) pulled back into range-shift support (38–50) |
| ⭐ 4 | Momentum | Daily RSI(14) turning up (today > yesterday) |
| ⭐ 5 | Trigger | Bullish reversal candle (hammer/engulfing/piercing) today |
| ⭐ 6 | Regime intact | Daily RSI(14) hasn't closed below 35 in the last 5 sessions |

**Scoring:** 6/6 = "Core Buy" (perfect setup) · 4-5/6 = "Watchlist" · <4 = Ignore.

Entry = signal-day close. Stop = signal-day low. Target = exit when daily RSI(14) closes back
at/above 60 (this is an RSI-level target, not a price target — that's Malkan's own documented
exit rule for this method, unlike a price-based swing-high target).

## Contents

- `screener.py` — production-ready Python scanner (yfinance + pandas_ta). Also has
  `load_nse_universe()` for building an NSE top-600 equity list (see below).
- `screener_fmp.py` — same scoring engine via Financial Modeling Prep's REST API instead of
  yfinance. **Requires an FMP plan with international/NSE exchange access.**
- `backtest.py` — walk-forward backtester, RSI-target-aware (see "Backtesting" below).
- `backtest_weekend_gtt.py` — backtests the specific real-world workflow: scan on Friday's close,
  6/6-only, enter Monday's open, fixed ₹60,000/trade, exit on a Supertrend-trail GTT (see
  "Weekend-scan / GTT backtest" below).
- `pinescript/malkan_gfs_rsi.pine` — TradingView Pine Script v5 indicator with dashboard + alerts.
- `sheets/FORMULAS.md` — Google Sheets / Excel no-code formula reference.
- `docs/ARCHITECTURE.md` — deployment architecture (scheduler → scan → alert pipeline).
- `docs/VALIDATION.md` — backtest / validation checklist before going live.

## NSE universe: top 600, equity only (no ETFs/derivatives)

```python
from screener import load_nse_universe
universe = load_nse_universe("EQUITY_L.csv", top_n=600)
```

Download NSE's own equity listing first — it already excludes ETFs and derivatives (neither is
in the EQ series / neither is a "listed" instrument in this file), so no separate filter is
needed beyond `SERIES == 'EQ'`, which `load_nse_universe()` applies automatically:

```bash
curl -o EQUITY_L.csv "https://archives.nseindia.com/content/equity/EQUITY_L.csv"
```

That file has no market-cap column, so "top 600 by market cap" needs a cap ranking joined in
separately (FMP profile data, NSE's own market-cap report, etc.) — pass its column name as
`market_cap_col` to rank before truncating; without it, `load_nse_universe()` just takes the
first 600 rows of the file as-is.

## Quick Start (Python, yfinance)

```bash
cd malkan-7star-prd
pip install -r requirements.txt
python screener.py
```

Edit `NSE_UNIVERSE` in `screener.py` (or use `load_nse_universe()` above) to set your stock
universe. Results with score >= 4/6 print to console and save to a CSV.

## Quick Start (Python, FMP)

```bash
cd malkan-7star-prd
pip install -r requirements.txt
export FMP_API_KEY=your_key_here
python screener_fmp.py --universe nse --limit 600   # top 600 active NSE equities from FMP
```

`screener_fmp.py` uses the same `historical-price-eod-full` shape verified live against FMP for
US tickers (via an FMP MCP connector, not this script directly — this dev environment has no
direct route to financialmodelingprep.com). The NSE-specific bits (`fetch_nse_universe()`, and
NSE data access itself) are still unverified — that connector's plan doesn't cover international
exchanges. Sanity-check against a couple of known NSE tickers before pointing it at the whole
exchange.

## Backtesting

```bash
cd malkan-7star-prd
python backtest.py AAPL.csv MSFT.csv NVDA.csv --min-score 6 --max-hold 60
```

Each CSV needs `date,open,high,low,close,volume` columns. See `docs/VALIDATION.md` for the full
pre-live checklist (slippage, sector-correlation caps, regime filters) — a backtest with no
transaction costs will overstate the edge.

**A real run** (AAPL/MSFT/NVDA, 2021–2026, no NSE access from this dev environment — see below):

| Min score | Trades | Win rate | Expectancy | Profit factor |
| :--- | :--- | :--- | :--- | :--- |
| 6/6 | 6 | 33% | −0.03R | 0.95 |
| 5/6 | 72 | 31% | +0.13R | 1.20 |
| 4/6 | 506 | 40% | **+0.56R** | **2.05** |

Caveats that matter: only 3 correlated US mega-cap tech names (not NSE, not diversified —
NVDA alone drove most of the total return); zero transaction costs modeled; 6/6's 6-trade sample
is too small to trust the direction, let alone the magnitude.

## Weekend-scan / GTT backtest

Backtests the actual intended workflow: scan Friday's close, 6/6-only, GTT buy for Monday's
open, fixed ₹60,000 per trade, exit on a Supertrend(10,3)-trailing GTT sell (see the module
docstring in `backtest_weekend_gtt.py` for the exact fill/trigger-timing rules).

```bash
cd malkan-7star-prd
python backtest_weekend_gtt.py AAPL.csv MSFT.csv NVDA.csv --years 6
```

**Two things to know before running this for real:**
1. **Zerodha GTT orders don't auto-update their trigger price.** This backtest models the
   Supertrend trigger trailing automatically every day — running the strategy for real means
   recalculating Supertrend and *modifying* the GTT order daily, not placing it once over the
   weekend.
2. **RSI-only entries and a Supertrend-only exit don't always agree.** The 6-star score has no
   trend/Supertrend requirement (correctly, per Malkan's actual RSI-only method — see above), so
   a real fraction of 6/6 signals fire while Supertrend has *already* flipped bearish. When that
   happens the GTT trigger (set from the signal Friday's Supertrend value) is already below
   Monday's open, and the position exits same-day for a wash.

**A real run** (13 US large-caps — AAPL, MSFT, NVDA, GOOGL, AMZN, META, TSLA, JPM, XOM, WMT,
NFLX, AMD, HD — 2019–2026, last 6 years scored/traded, no NSE access from this dev environment):

- **8 trades total** across 13 stocks over 6 years — 6-star-only, Friday-only scanning is very
  restrictive. 5 of those 8 exited same-day at ~breakeven via the mechanism above (confirmed by
  inspecting the raw data, not a bug — NVDA's 2025-11-07 signal fired the Friday after Supertrend
  had already flipped from 188.9 to 206.5, well above price).
- Win rate 12.5%, total P&L on ₹4.79L invested across those 8 trades: **−₹440** (net roughly
  flat — the sample is far too small to call this a real result either way).

The honest conclusion from this run isn't "the strategy loses money" — it's that **8 trades in 6
years across 13 large-caps is not a sample**, and more than half of what few signals exist get
immediately neutralized by the entry/exit rules disagreeing with each other. Two ways to actually
test this: run it against the real NSE top-600 (600 stocks instead of 13 should produce a lot
more signals), or reconsider requiring price above Supertrend as part of entry so the exit rule
isn't fighting the entry rule from day one.

## Why "PRD" got dropped — research sources

Vishal Malkan's actual, extensively documented method:
- [A Complete Guide To 5-Star RSI Strategy Ft. Vishal B Malkan](https://blog.elearnmarkets.com/a-5-star-rsi-strategy/)
- [RSI 7 Star Strategy — Chartink screener](https://chartink.com/screener/rsi-7-star-strategy-vishal-malkan)
- [Seven Star Malkan BUY setup (Grandfather-Father-Son) — Chartink screener](https://chartink.com/screener/seven-star-malkan-buy-setup-grandfather-father-son-for-passive-traders-sell-rules)
- [60-40 RSI Strategy / 5-Star Swing Trading writeup](https://forexvp.com/forex-trading-systems-free-download/60-40-rsi-strategy-5-star-swing-trading-strategy-free-download/)

No public source ties "PRD" to Malkan specifically. If you have a definition from one of his
paid courses/PDFs that these public sources don't cover, that's the one to build against instead
— tell me the exact rules and this gets rebuilt around them.

## Disclaimer

Not financial advice. The exact star-rated criteria taught in Malkan's paid courses may differ
from this public-source reconstruction in ways that matter — validate with your own backtests
(and against course material, if you have access to it) before trading real capital.
