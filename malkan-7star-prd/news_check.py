"""
News/sentiment sanity-check for high-scoring Malkan GFS RSI signals, via
OmniRoute (this repo's local LLM gateway -- see the repo root README.md)
instead of calling a single AI provider directly.

The 6-star score is pure price/RSI action -- it has never looked at a single
headline. For each stock scoring at or above --min-score, this fetches
recent news and asks an LLM to flag things a technical signal can't see:
earnings miss, guidance cut, fraud/regulatory action, accounting
irregularities, a management scandal, an active short-seller report. A
flagged stock isn't disqualified -- this is a sanity check layered on top of
the star score, not a replacement for it.

Setup (verified working in this dev environment):
    npm install && npm start        # from the repo root, not this directory
Then open http://localhost:20128 and connect at least one provider. The
server itself starts cleanly and serves an OpenAI-compatible
/v1/chat/completions endpoint with zero auth needed for local requests --
confirmed by hitting it directly. What ISN'T verified end-to-end: an actual
completion succeeding, because this sandbox has no outbound route to any of
OmniRoute's pre-wired providers (opencode, felo-web) or to whatever provider
you connect via the dashboard -- same network restriction that blocks NSE
data elsewhere in this project. On your own machine, with real internet,
this should just work once a provider is connected.

News source: FMP's news endpoints (a Starter-tier-or-higher plan -- see
screener_fmp.py for why the free tier doesn't cover this either). Swap
fetch_headlines() for a different provider if you don't have that.

Usage:
    export FMP_API_KEY=your_key_here      # for headlines
    npm start                             # in another terminal, from repo root
    python news_check.py malkan_gfs_scan_20260824.csv --min-score 5
"""

import argparse
import json
import os
from datetime import datetime, timedelta

import pandas as pd
import requests

OMNIROUTE_BASE_URL = os.environ.get("OMNIROUTE_BASE_URL", "http://localhost:20128/v1")
OMNIROUTE_API_KEY = os.environ.get("OMNIROUTE_API_KEY", "")  # not required for local requests
OMNIROUTE_MODEL = os.environ.get("OMNIROUTE_MODEL", "auto")

FMP_BASE = "https://financialmodelingprep.com/stable"
FMP_API_KEY = os.environ.get("FMP_API_KEY")

NEWS_CHECK_MIN_SCORE = 5
NEWS_LOOKBACK_DAYS = 10
MAX_HEADLINES = 10


def fetch_headlines(symbol, days=NEWS_LOOKBACK_DAYS, limit=MAX_HEADLINES):
    if not FMP_API_KEY:
        raise RuntimeError("Set FMP_API_KEY (a plan with news access) to fetch headlines.")
    to_date = datetime.now().date()
    from_date = to_date - timedelta(days=days)
    resp = requests.get(
        f"{FMP_BASE}/news/search-stock-news",
        params={
            "symbols": symbol, "from": from_date.isoformat(), "to": to_date.isoformat(),
            "limit": limit, "apikey": FMP_API_KEY,
        },
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    return [
        {"date": a.get("publishedDate", ""), "title": a.get("title", "")}
        for a in data
    ]


def check_headlines(ticker, headlines):
    """Send headlines to an LLM via OmniRoute and get back a red-flag verdict."""
    if not headlines:
        return {"flag": False, "reason": "no recent headlines found", "headlines_reviewed": 0}

    listing = "\n".join(f"- [{h['date']}] {h['title']}" for h in headlines)
    prompt = (
        f"You are a risk-check filter for a technical stock screener. The screener already "
        f"found a bullish RSI setup on {ticker} purely from price action -- it has NOT looked "
        f"at any news or fundamentals. Your only job is to scan these recent headlines for red "
        f"flags a technical signal would miss: earnings miss, guidance cut, fraud/regulatory/"
        f"legal action, accounting irregularities, a major management departure/scandal, or an "
        f"active short-seller/investigation report. Ignore routine or neutral news.\n\n"
        f"Headlines:\n{listing}\n\n"
        f'Respond with ONLY a JSON object: {{"flag": true/false, "reason": "one sentence"}}'
    )

    headers = {"Content-Type": "application/json"}
    if OMNIROUTE_API_KEY:
        headers["Authorization"] = f"Bearer {OMNIROUTE_API_KEY}"

    resp = requests.post(
        f"{OMNIROUTE_BASE_URL}/chat/completions",
        headers=headers,
        json={
            "model": OMNIROUTE_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
        },
        timeout=60,
    )
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"]
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        parsed = {"flag": None, "reason": f"LLM did not return valid JSON: {content[:200]}"}
    parsed["headlines_reviewed"] = len(headlines)
    return parsed


def enrich(csv_path, min_score):
    df = pd.read_csv(csv_path)
    flags, reasons, counts = [], [], []
    for _, row in df.iterrows():
        try:
            num_score = int(str(row["Score"]).split("/")[0])
        except (ValueError, KeyError):
            num_score = 0
        if num_score < min_score:
            flags.append(None)
            reasons.append("below --min-score, not checked")
            counts.append(0)
            continue

        ticker = row["Ticker"]
        print(f"Checking news for {ticker}...")
        try:
            headlines = fetch_headlines(ticker)
            result = check_headlines(ticker, headlines)
        except Exception as e:
            result = {"flag": None, "reason": f"error: {e}", "headlines_reviewed": 0}
        flags.append(result.get("flag"))
        reasons.append(result.get("reason"))
        counts.append(result.get("headlines_reviewed", 0))

    df["NewsFlag"] = flags
    df["NewsReason"] = reasons
    df["HeadlinesReviewed"] = counts

    out_path = csv_path.replace(".csv", "_news_checked.csv")
    df.to_csv(out_path, index=False)
    print(f"\nSaved {out_path}")

    flagged = df[df["NewsFlag"] == True]  # noqa: E712 -- comparing against a nullable bool column
    if len(flagged):
        print(f"\n{len(flagged)} stock(s) flagged:")
        for _, r in flagged.iterrows():
            print(f"  {r['Ticker']}: {r['NewsReason']}")
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv", help="A screener.py output CSV (malkan_gfs_scan_*.csv)")
    parser.add_argument("--min-score", type=int, default=NEWS_CHECK_MIN_SCORE,
                         help=f"only news-check stocks scoring at least this many stars (default {NEWS_CHECK_MIN_SCORE})")
    args = parser.parse_args()
    enrich(args.csv, args.min_score)
