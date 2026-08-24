# Deployment Architecture (Professional Grade)

```mermaid
graph TD
    A[Scheduler: 09:15 AM / 03:30 PM IST] --> B(Python Runner / GitHub Actions / AWS Lambda)
    B --> C{Data Source}
    C -->|Primary| D[NSE Python Library / yfinance]
    C -->|Backup| E[Alpha Vantage / Twelve Data]
    B --> F[Calculate 6 Stars: RSI Cascade + Candle Trigger]
    F --> G[Filter Score >= 4]
    G --> H[Enrich: Fundamentals / Open Interest]
    H --> I[Output: CSV / PostgreSQL / Google Sheet]
    I --> J[Telegram Bot / Email / Dashboard]
    J --> K[Trader Execution]
```

## Notes

- **Scheduler:** run once pre-market (09:15 IST) for the day's watchlist, and once near the
  close (15:30 IST) to catch late-session reversal candles.
- **Data source fallback:** `yfinance` is free but occasionally rate-limited; wire a secondary
  provider (Alpha Vantage / Twelve Data / an NSE-specific library) so a single provider outage
  doesn't blank the scan.
- **Enrichment (optional):** attach fundamentals (P/E, sector weight) or F&O open interest data
  before dispatch, so signals can be filtered further (e.g. exclude illiquid names).
- **Dispatch:** push filtered results to a Telegram bot / email digest / internal dashboard
  rather than requiring someone to run the script manually.
