#!/usr/bin/env python3
"""Job Radar portal fetcher: direct HTTPS, standard library only (no connectors).

Usage:
  python3 fetch.py portals [--out candidates.json]   # Tier 1a portals from sources.yaml
  python3 fetch.py board greenhouse <token> | lever <company>   # one ATS board (Tier 1b follow-up)
  python3 fetch.py jd <url>                          # one job description as plain text

`portals` writes {"candidates": [...], "sources_status": [...]} where each candidate is
{company, title, location, url, source, posted, tier, snippet, group}, which score.py reads.
A portal that fails is recorded in sources_status with its error, and the run carries on.
Hosts must be allowed by the session's environment ("test24 – Job Radar").
"""
import html
import json
import os
import re
import ssl
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
TIMEOUT = 25


def _ctx():
    for ca in (os.environ.get("SSL_CERT_FILE"), "/root/.ccr/ca-bundle.crt"):
        if ca and os.path.exists(ca):
            return ssl.create_default_context(cafile=ca)
    return ssl.create_default_context()


CTX = _ctx()


def get(url, data=None, headers=None):
    h = {"User-Agent": UA, "Accept": "application/json, text/html;q=0.9, */*;q=0.8", "Accept-Language": "en-US,en;q=0.9"}
    if data is not None:
        data = json.dumps(data).encode()
        h["Content-Type"] = "application/json"
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h)
    with urllib.request.urlopen(req, timeout=TIMEOUT, context=CTX) as r:
        return r.read().decode("utf-8", "replace")


def text_of(fragment):
    s = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", fragment)
    s = re.sub(r"(?i)<br\s*/?>|</(p|li|div|h\d|tr)>", "\n", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t\r\f\v]+", " ", s)
    return re.sub(r"\n\s*\n+", "\n", s).strip()


def cand(p, title, location="", url="", posted="", snippet="", company=None):
    return {"company": company or p["name"], "title": (title or "").strip(), "location": (location or "").strip(),
            "url": url, "source": p["name"] + " careers", "posted": posted or "", "tier": "1a",
            "snippet": (snippet or "")[:300], "group": p.get("group", "other")}


# ---------------------------------------------------------------- adapters ---
def ad_amazon(p, q):
    url = f"https://www.amazon.jobs/en/search.json?base_query={urllib.parse.quote(q)}&country=IND&result_limit=50&sort=recent"
    out = []
    for j in json.loads(get(url)).get("jobs", []):
        out.append(cand(p, j.get("title"), j.get("normalized_location") or j.get("location"),
                        "https://www.amazon.jobs" + (j.get("job_path") or ""), j.get("posted_date", ""),
                        text_of(j.get("description_short") or "")))
    return out


def ad_eightfold(p, q):
    url = (f"https://explore.jobs.netflix.net/api/apply/v2/jobs?domain=netflix.com&query={urllib.parse.quote(q)}"
           f"&location=India&num=50&sort_by=new")
    out = []
    for j in json.loads(get(url)).get("positions", []):
        posted = ""
        if j.get("t_create"):
            posted = datetime.fromtimestamp(j["t_create"], timezone.utc).date().isoformat()
        link = j.get("canonicalPositionUrl") or f"https://explore.jobs.netflix.net/careers/job/{j.get('id')}"
        loc = j.get("location") or ", ".join(j.get("locations") or [])
        out.append(cand(p, j.get("name"), loc, link, posted, j.get("department", "")))
    return out


def ad_workday(p, q):
    host, tenant, site = p["host"], p["tenant"], p["site"]
    body = {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": q}
    data = json.loads(get(f"https://{host}/wday/cxs/{tenant}/{site}/jobs", data=body))
    out = []
    for j in data.get("jobPostings", []):
        out.append(cand(p, j.get("title"), j.get("locationsText", ""),
                        f"https://{host}/en-US/{site}{j.get('externalPath', '')}", j.get("postedOn", ""),
                        " ".join(j.get("bulletFields") or []), company=p.get("company")))
    return out


def ad_jibe(p, q):
    base = p["base"].rstrip("/")
    url = f"{base}/api/jobs?keywords={urllib.parse.quote(q)}&location=India&page=1&sortBy=posted_date&descending=true&internal=false"
    out = []
    for row in json.loads(get(url)).get("jobs", []):
        j = row.get("data", row)
        company = j.get("hiring_organization") or (j.get("tags1") or [None])[0] or p.get("company")
        loc = j.get("full_location") or ", ".join(x for x in (j.get("city"), j.get("country")) if x)
        slug = j.get("slug") or j.get("req_id")
        out.append(cand(p, j.get("title"), loc, f"{base}/jobs/{slug}", (j.get("posted_date") or "")[:10],
                        text_of(j.get("description") or "")[:300], company=company))
    return out


def ad_google(p, q):
    url = (f"https://www.google.com/about/careers/applications/jobs/results/?q={urllib.parse.quote(q)}"
           f"&location=India&sort_by=date&hl=en_US")
    page = get(url, headers={"Accept": "text/html"})
    out, seen = [], set()
    for m in re.finditer(r'href="(?:\./)?jobs/results/(\d+)-([a-z0-9-]+)[^"]*"', page):
        jid, slug = m.groups()
        if jid in seen:
            continue
        seen.add(jid)
        # Title and location sit in the block just before the link
        block = page[max(0, m.start() - 4000):m.start()]
        titles = re.findall(r"<h3[^>]*>(.*?)</h3>", block, re.S)
        title = text_of(titles[-1]) if titles else slug.replace("-", " ").title()
        locs = re.findall(r"place</i>\s*<span[^>]*>(.*?)</span>|<span class=\"r0wTof[^\"]*\">(.*?)</span>", block, re.S)
        loc = text_of(next((a or b for a, b in reversed(locs)), "")) if locs else ""
        out.append(cand(p, title, loc, f"https://www.google.com/about/careers/applications/jobs/results/{jid}-{slug}"))
    return out


def ad_generic(p, q):
    """Plain HTML: links whose text looks like a creative-leadership title."""
    url = p["url"].replace("{q}", urllib.parse.quote(q))
    page = get(url, headers={"Accept": "text/html"})
    out = []
    for m in re.finditer(r'<a\b[^>]*href="([^"#]+)"[^>]*>(.*?)</a>', page, re.S | re.I):
        t = text_of(m.group(2))
        if 5 < len(t) < 140 and re.search(r"creative|art director|design director|brand", t, re.I):
            out.append(cand(p, t, "", urllib.parse.urljoin(url, html.unescape(m.group(1)))))
    if not out and len(page) < 200000 and "<script" in page and "</a>" not in page[:200000]:
        raise RuntimeError("page renders in JavaScript; use the search fallback")
    return out


def board_greenhouse(token):
    data = json.loads(get(f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs"))
    return [{"company": token, "title": j.get("title", ""), "location": (j.get("location") or {}).get("name", ""),
             "url": j.get("absolute_url", ""), "source": "Greenhouse", "posted": (j.get("updated_at") or "")[:10],
             "tier": "1b", "snippet": "", "group": "other"} for j in data.get("jobs", [])]


def board_lever(company):
    data = json.loads(get(f"https://api.lever.co/v0/postings/{company}?mode=json"))
    out = []
    for j in data:
        posted = datetime.fromtimestamp(j["createdAt"] / 1000, timezone.utc).date().isoformat() if j.get("createdAt") else ""
        out.append({"company": company, "title": j.get("text", ""), "location": (j.get("categories") or {}).get("location", ""),
                    "url": j.get("hostedUrl", ""), "source": "Lever", "posted": posted, "tier": "1b",
                    "snippet": "", "group": "other"})
    return out


ADAPTERS = {"amazon": ad_amazon, "eightfold": ad_eightfold, "workday": ad_workday, "jibe": ad_jibe,
            "google": ad_google, "generic": ad_generic}


# ---------------------------------------------------------------- commands ---
def load_sources():
    import yaml  # PyYAML; `pip install pyyaml` if missing
    return yaml.safe_load((HERE / "sources.yaml").read_text())


def cmd_portals(out_path):
    src = load_sources()
    queries = src.get("portal_queries", ["creative director"])
    cands, status = [], []
    for p in src["portals"]:
        fn = ADAPTERS.get(p.get("adapter", "generic"))
        n, errs = 0, []
        for q in p.get("queries", queries):
            try:
                rows = fn(p, q)
                cands += rows
                n += len(rows)
            except Exception as e:  # one bad portal never stops the run
                errs.append(f"{q}: {type(e).__name__}: {str(e)[:120]}")
        status.append({"name": p["name"], "ok": n > 0 or not errs, "count": n, "errors": errs[:2],
                       "fallback_search": p.get("fallback_search", "")})
    Path(out_path).write_text(json.dumps({"candidates": cands, "sources_status": status}, indent=1, ensure_ascii=False))
    for s in status:
        print(f"{'OK ' if s['ok'] else 'ERR'} {s['count']:4d}  {s['name']}" + (f"  [{s['errors'][0]}]" if s["errors"] else ""))
    print(f"{len(cands)} raw candidates -> {out_path}")


def cmd_jd(url):
    """Print a JD as text. Workday uses its JSON API; other sites use JSON-LD, then the page text."""
    m = re.match(r"https://([^/]+\.myworkdayjobs\.com)/(?:[a-z]{2}-[A-Z]{2}/)?([^/]+)/(job/.+)", url)
    if m:
        host, site, rest = m.groups()
        tenant = host.split(".")[0]
        d = json.loads(get(f"https://{host}/wday/cxs/{tenant}/{site}/{rest}"))
        info = d.get("jobPostingInfo", {})
        print(f"TITLE: {info.get('title','')}\nLOCATION: {info.get('location','')}\nPOSTED: {info.get('postedOn','')}\n")
        print(text_of(info.get("jobDescription", ""))[:9000])
        return
    page = get(url, headers={"Accept": "text/html"})
    for blob in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', page, re.S):
        try:
            data = json.loads(blob)
        except ValueError:
            continue
        for d in data if isinstance(data, list) else [data]:
            if isinstance(d, dict) and d.get("@type") == "JobPosting":
                loc = d.get("jobLocation")
                loc = loc[0] if isinstance(loc, list) and loc else loc
                addr = (loc or {}).get("address", {}) if isinstance(loc, dict) else {}
                print(f"TITLE: {d.get('title','')}\nCOMPANY: {(d.get('hiringOrganization') or {}).get('name','')}\n"
                      f"LOCATION: {addr.get('addressLocality','')} {addr.get('addressCountry','')}\nPOSTED: {d.get('datePosted','')}\n")
                print(text_of(d.get("description", ""))[:9000])
                return
    main = re.search(r"(?is)<main[^>]*>(.*?)</main>", page)
    print(text_of(main.group(1) if main else page)[:9000])


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "portals":
        cmd_portals(a[a.index("--out") + 1] if "--out" in a else "candidates.json")
    elif a[0] == "board" and len(a) == 3:
        rows = board_greenhouse(a[2]) if a[1] == "greenhouse" else board_lever(a[2])
        print(json.dumps(rows, indent=1, ensure_ascii=False))
    elif a[0] == "jd" and len(a) == 2:
        cmd_jd(a[1])
    else:
        sys.exit(__doc__)
