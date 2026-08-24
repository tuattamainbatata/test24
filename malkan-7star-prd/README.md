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
- `news_check.py` — post-scan LLM sanity check via OmniRoute (this repo's local AI gateway, see
  the repo root README.md): flags high-scoring signals with recent bad news the RSI score
  can't see (see "News/sentiment sanity check" below).
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

**First run** (13 US large-caps — AAPL, MSFT, NVDA, GOOGL, AMZN, META, TSLA, JPM, XOM, WMT, NFLX,
AMD, HD — 2019–2026, last 6 years scored/traded, no NSE access from this dev environment) found
only 8 trades total, 5 of which exited same-day at ~breakeven via the mechanism above (confirmed
against raw data — NVDA's 2025-11-07 signal fired the Friday after Supertrend had already flipped
from 188.9 to 206.5, well above price). Net P&L: −₹440 on ₹4.79L invested — not a real result
either way, just too few trades.

### Refinement: require Supertrend already bullish at entry (now the default)

`backtest_weekend_gtt.py` now skips signals where Supertrend has already flipped bearish on the
signal day by default (`--allow-any-trend` to disable). This is a strict improvement, not a
tradeoff — it only ever removes trades that were mathematically dead on arrival: on the 6/6-only
sample above it dropped exactly the 6 zero-PnL trades and kept the one winner (+₹537) and one
loser (−₹977) unchanged, confirming the mechanism rather than coincidence.

That still leaves only 2 trades at strict 6/6 across 13 stocks — nowhere near enough to trust.
Loosening `--min-score` (still keeping the uptrend filter) unlocks a much larger sample on the
same real data:

| Variant | Trades | Win rate | Total P&L | Avg P&L/trade | Avg win | Avg loss | Max drawdown |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 6/6 + uptrend filter | 2 | 50% | −₹440 | −0.4% | +0.9% | −1.6% | ₹0 |
| 5/6 + uptrend filter | 45 | 40% | **+₹61,131** | +2.3% | +11.7% | −4.1% | −₹15,439 |
| 4/6 + uptrend filter | 202 | 39% | **+₹317,643** | +2.6% | +13.7% | −4.5% | −₹30,733 |
| 5/6, no uptrend filter | 92 | 21% | +₹108,519 | +2.0% | +14.6% | −1.3% | — |
| 4/6, no uptrend filter | 510 | 16% | +₹311,985 | +1.0% | +13.5% | −1.3% | — |

Reading this: the uptrend filter improves quality at every score level (higher win rate, better
avg P&L per trade), and once combined with a looser score threshold there's finally a real
sample — 45-202 trades over 6 years, a classic trend-following profile (win less than half the
time, but winners average 3x the size of losers), positive on every variant tested. Average
holding period jumped to 35-39 days (vs. ~3 days in the original 6/6-only run) — once entries
only fire in a confirmed uptrend, the Supertrend exit takes longer to trigger.

**This is real evidence, but it changes your "only 6 star" rule** — that's a decision for you,
not something to silently swap in. Two ways to reconcile it: (a) accept 4/6 or 5/6 as "perfect
enough" for this specific GTT workflow, since the extra stars (candle trigger timing, momentum
turning up) matter less once the trend filter is doing the real work of picking good entries; or
(b) keep strict 6/6 and scale up the universe instead — 13 stocks is a thin sample by
construction, and the real NSE top-600 (46x more names) should produce proportionally more
signals even at the strict threshold. Both are worth testing once NSE data access exists; only
(a) is testable from this dev environment.

Caveats that still apply regardless of variant: not NSE data: no transaction costs/slippage; no
capital-pool cap across simultaneous positions (each ticker gets its own independent
₹60,000 budget, so total capital needed scales with how many signals overlap); Zerodha GTT
doesn't auto-trail, so running this for real means modifying the order daily.

## News/sentiment sanity check (via OmniRoute)

The 6-star score is pure price/RSI action — it has never read a single headline. A technically
perfect setup can still be a stock that just missed earnings or is under a fraud investigation.
`news_check.py` closes that gap: for each stock scoring at or above `--min-score` in a
`screener.py` output CSV, it pulls recent headlines and asks an LLM (via this repo's local
OmniRoute gateway — see the root [README.md](../README.md)) to flag anything a technical signal
wouldn't catch: earnings miss, guidance cut, fraud/regulatory action, accounting irregularities,
a management scandal, an active short-seller report. A flag doesn't disqualify the stock — it's a
sanity check layered on top of the star score, printed alongside it, not a veto.

```bash
# from the repo root
npm install
npm start                 # leave running in its own terminal; dashboard at localhost:20128
```

Open the dashboard and connect at least one AI provider (any of the 90+ free-tier options work),
then:

```bash
cd malkan-7star-prd
export FMP_API_KEY=your_key_here   # for headlines -- needs a plan with news access
python news_check.py malkan_gfs_scan_20260824.csv --min-score 5
```

**What's actually verified here vs. what isn't:** the OmniRoute server itself starts cleanly in
this dev environment and serves a working OpenAI-compatible `/v1/chat/completions` endpoint with
zero auth needed for local requests — confirmed by hitting it directly. What's *not* verified
end-to-end is an actual completion succeeding: this sandbox has no outbound route to any of
OmniRoute's pre-wired providers (opencode, felo-web) or to whatever you connect via the
dashboard, the same network restriction that blocks NSE data everywhere else in this project.
Sending a real request through `news_check.py`'s `check_headlines()` against the live local
server reached OmniRoute fine and failed only at the provider-fetch step (`HTTPError 500:
fetch failed`) — exactly the expected shape of "code is correct, environment has no internet."
On your own machine, with a connected provider, this should just work.

FMP's news endpoints are gated the same way its NSE price data is (see `screener_fmp.py`) — a
Starter-tier-or-higher plan, not the free tier. Swap `fetch_headlines()` for a different news
source if you don't have that.

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
