# Validation Checklist (Before Going Live)

1. **Backtest.** Run the screener over a historical window (e.g. `2023-01-01` to `2024-01-01`)
   and track win rate and expectancy per signal.
   - Target: win rate > 45%, realized risk:reward > 1.8.
2. **Slippage test.** Assume 0.2% slippage + 0.03% brokerage + STT. Does the edge survive?
3. **Correlation check.** Are 80%+ of signals coming from a single sector? Cap exposure (e.g.
   max 3 positions per sector) if so.
4. **Market regime filter.** Do not trade new signals if Nifty < 200 EMA or India VIX > 20 —
   preserve cash in a hostile regime rather than forcing setups.
