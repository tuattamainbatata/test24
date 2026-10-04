#!/usr/bin/env python3
"""Job Radar first-pass filter: title/location match, dedupe against seen.json, and a provisional bucket.

Usage:
  python3 score.py filter candidates.json > shortlist.json
  python3 score.py mark shortlist.json        # record shortlisted + rejected keys in seen.json

In the nightly routine, seen.json is rebuilt from the Job Radar tracker's db before filtering
(see ROUTINE.md). The tracker is the source of truth, and the copy in git only seeds local runs.
  python3 score.py key "Company" "Title" "City"

candidates.json is a list of objects shaped like
  {"company", "title", "location", "url", "source", "posted", "tier", "snippet"}.
tier is one of "1a", "1b", "2" or "3". Tier 3 items (trade-press signals) skip the title filter.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEEN = HERE / "seen.json"

# Title patterns, strongest first: (regex, points)
TITLE_RULES = [
    (r"\b(executive creative director|ecd|chief creative|national creative director|head of creative|creative head)\b", 50),
    (r"\b(group|senior|sr\.?) creative director\b", 42),
    (r"\bassociate executive creative director\b", 40),
    (r"\b(head of (brand|design|creative studio)|brand creative (lead|director)|creative studio (lead|head))\b", 40),
    (r"\bcreative director\b", 35),
    (r"\b(intelligent creativity|head.{0,25}(content|creativ)|creative (technology|innovation) (head|lead))\b", 30),
    (r"\b(creative lead|design director|director,? (brand|creative)|film (and|&) series marketing)\b", 28),
    (r"\bart director\b", 15),
]
# Titles that can never match
EXCLUDE = re.compile(
    r"\b(engineer|engineering|developer|product manager|program manager|sales|account manager|finance|"
    r"technician|intern|trainee|analyst|recruiter|banquet|legal|hr\b|data|security|scientist|"
    r"associate creative director|junior|jr\.?|executive director - |media planner|performance marketing)\b",
    re.I,
)
ART_BONUS = re.compile(r"\b(art|design|visual|craft|typograph)", re.I)
COPY_PENALTY = re.compile(r"\bcopy\b", re.I)

PRIMARY = re.compile(r"mumbai|navi mumbai|thane|bengaluru|bangalore|india\s*[-,]?\s*remote|remote", re.I)
ALSO_SEEN = re.compile(r"dubai|abu dhabi|uae|riyadh|saudi|doha|qatar|mena|middle east", re.I)
INDIA_OTHER = re.compile(r"gurgaon|gurugram|delhi|noida|hyderabad|chennai|pune|kolkata|india", re.I)

# Prefer company portals over boards when the same role turns up in several places
SOURCE_RANK = {"1a": 0, "1b": 1, "2": 2, "3": 3}


def norm(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"\(.*?\)|[^a-z0-9 ]+", " ", s)
    s = re.sub(r"\b(the|pvt|ltd|limited|india|inc|llp|group|worldwide)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def city(loc: str) -> str:
    loc = (loc or "").lower()
    for c in ("mumbai", "thane", "bengaluru", "bangalore", "remote", "dubai", "abu dhabi", "gurugram", "gurgaon", "delhi", "hyderabad", "chennai", "pune"):
        if c in loc:
            return {"bangalore": "bengaluru", "gurgaon": "gurugram"}.get(c, c)
    return norm(loc)[:20]


def key(company: str, title: str, loc: str) -> str:
    raw = f"{norm(company)}|{norm(title)}|{city(loc)}"
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


def title_points(title: str) -> int:
    if EXCLUDE.search(title or ""):
        return 0
    for rx, pts in TITLE_RULES:
        if re.search(rx, title or "", re.I):
            return pts
    return 0


def location_class(loc: str, snippet: str = "") -> str:
    text = f"{loc} {snippet}"
    if PRIMARY.search(loc or ""):
        return "primary"
    if ALSO_SEEN.search(loc or ""):
        return "also_seen"
    if INDIA_OTHER.search(loc or "") and re.search(r"remote|hybrid", text, re.I):
        return "primary"
    if INDIA_OTHER.search(loc or ""):
        return "india_other"
    if not loc and PRIMARY.search(snippet or ""):
        return "primary"
    if not loc:
        return "unknown"  # location not stated in the search excerpt: check the JD
    return "other"


def load_seen() -> dict:
    if SEEN.exists():
        return json.loads(SEEN.read_text())
    return {"keys": {}}


def cmd_filter(path: str) -> None:
    items = json.loads(Path(path).read_text())
    seen = load_seen()["keys"]
    out: dict[str, dict] = {}
    rejected = []
    for it in items:
        tier = str(it.get("tier", "2"))
        k = it.get("key") or key(it.get("company", ""), it.get("title", ""), it.get("location", ""))
        it["key"] = k
        if k in seen:
            continue
        if tier == "3":
            it["bucket"] = "signal"
            it["prelim"] = 0
        else:
            pts = title_points(it.get("title", ""))
            lc = location_class(it.get("location", ""), it.get("snippet", ""))
            it["location_class"] = lc
            if pts == 0 or lc in ("other",):
                rejected.append(k)
                continue
            text = f"{it.get('title','')} {it.get('snippet','')}"
            if ART_BONUS.search(text):
                pts += 8
            if COPY_PENALTY.search(it.get("title", "")):
                pts -= 10
            pts += {"primary": 30, "also_seen": 10, "india_other": 5, "unknown": 5}[lc]
            it["prelim"] = pts
            if lc == "also_seen":
                it["bucket"] = "also_seen"
            elif lc in ("india_other", "unknown"):
                it["bucket"] = "watch"
            else:
                it["bucket"] = "candidate"  # final 🔥/👀 is set after the JD rating
        if k in out:
            # Same role found in another source: merge, keeping the most direct link
            prev = out[k]
            srcs = sorted(set(prev.get("sources", [prev.get("source")]) + [it.get("source")]) - {None})
            better = it if SOURCE_RANK.get(tier, 9) < SOURCE_RANK.get(str(prev.get("tier")), 9) else prev
            better["sources"] = srcs
            out[k] = better
        else:
            it["sources"] = [it.get("source")] if it.get("source") else []
            out[k] = it
    result = sorted(out.values(), key=lambda x: (x["bucket"] != "candidate", -x.get("prelim", 0)))
    json.dump({"shortlist": result, "rejected_keys": rejected}, sys.stdout, indent=1, ensure_ascii=False)


def cmd_mark(path: str) -> None:
    data = json.loads(Path(path).read_text())
    seen = load_seen()
    from datetime import date
    today = date.today().isoformat()
    for it in data.get("shortlist", []):
        seen["keys"].setdefault(it["key"], {"t": it.get("title", "")[:60], "c": it.get("company", "")[:40], "d": today})
    for k in data.get("rejected_keys", []):
        seen["keys"].setdefault(k, {"d": today, "r": 1})
    SEEN.write_text(json.dumps(seen, indent=0, ensure_ascii=False, sort_keys=True))
    print(f"seen.json now holds {len(seen['keys'])} keys")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd = sys.argv[1]
    if cmd == "filter":
        cmd_filter(sys.argv[2])
    elif cmd == "mark":
        cmd_mark(sys.argv[2])
    elif cmd == "key":
        print(key(*sys.argv[2:5]))
    else:
        sys.exit(__doc__)
