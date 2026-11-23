# Job Radar: nightly run (standalone instructions, no connectors needed)

You are running Ganeysh Nayak's nightly Job Radar. Ganeysh is a Group Creative Director at Ogilvy Mumbai, art-led, aiming for ECD or Head of Creative.

Work through the steps below in order. End with the short summary in step 6, which becomes the push/email notification.

- **Tracker:** https://claude.ai/artifact/To2mfQ9xiNNQa6ETYNccmB. It has a `db` with collections `jobs`, `runs` and `meta`. Write to it with the `ArtifactData` tool; load that tool with ToolSearch.
- **Repo:** the files live in `jobwatch/` on branch `claude/resume-career-progression-j9wclz`.
- **Fetching:** use `jobwatch/fetch.py` for direct HTTPS, and the built-in **WebSearch** tool for searches.
  - This session runs in the "test24 – Job Radar" environment, which allows the portal hosts listed in `sources.yaml`.
  - No connector (Firecrawl, Drive, Indeed) is needed. Don't stop if they are missing.
- **Never** scrape LinkedIn, Glassdoor or Naukri pages. For job boards, use the search-result titles and snippets only.

## 0. Prepare
1. Run `pip install -q pyyaml` if `import yaml` fails.
2. Read `jobwatch/sources.yaml`, `jobwatch/rate.md` and `jobwatch/resume_snapshot.md`. The snapshot is the résumé to rate against.
   - If the Google Docs `read_doc` tool happens to be available, read the live résumé `1S6F-3CW1YCu2UV2yowj4Xtrzi7F-HIey954Gvpo1MBs` instead, and note in the run record which one you used.
3. Build the dedupe list from the tracker:
   - `ArtifactData list` on collection `jobs`. Page with `query.cursor` until done; each doc id is a key already seen.
   - `ArtifactData get` on `meta`/`rejected`, which holds `{"keys": {key: date}}`. It may not exist yet.
   - Write the combined keys to `jobwatch/seen.json` as `{"keys": {key: {}}}`.

## 1. Collect candidates
Keep only postings and stories from the **last 2 days**.

**Look-back override:** if the run's extra text sets `LOOKBACK_DAYS=<n>`, use n days instead. That's Ganeysh's explicit request, so apply it as given and don't second-guess it from the run history. Keep only roles that are still open, and in step 3 rate up to 25 instead of 15.

- **Tier 1a, company portals:** run `python3 jobwatch/fetch.py portals --out /tmp/portals.json`.
  - For each portal that reports ERR or 0 jobs and has a `fallback_search` in `sources.yaml`, run that query with WebSearch.
  - Add those hits to the candidate list, setting `tier` to "1a" and `source` to "<portal> (search)".
- **Tier 1b, ATS sweep:** for each `ats_domains` entry, run WebSearch with `ats_query` plus the current month and year, and `allowed_domains: [domain]`.
  - Take the company and title from each result.
  - For a Greenhouse or Lever company, `python3 jobwatch/fetch.py board greenhouse <token>` (or `lever <company>`) lists the whole board. The token is the path segment after the domain.
- **Tier 2, job boards:** run each `board_queries` entry with WebSearch, using its `domains` as `allowed_domains`.
  - For Glassdoor results, also note the company rating (e.g. "3.4 ★") when the snippet shows it.
  - Prefer the company's own portal link when the same role is on one.
- **Boutiques:** run one WebSearch per entry in `boutiques`: `"<name>" hiring creative <Month Year>`.
- **Tier 3, trade-press signals:** run each `signal_queries` entry with WebSearch.
  - Keep only India or MENA creative-leadership moves, account wins and office openings that could open a seat for Ganeysh.
  - Write them as `tier` "3" with a one-line headline as the title. The company is the agency where a seat may open.

Merge every hit into one file, `/tmp/candidates.json`, as a JSON list of `{company, title, location, url, source, posted, tier, snippet, group}`. The portal hits are the `candidates` array from `/tmp/portals.json`.

## 2. Filter and dedupe
Run `python3 jobwatch/score.py filter /tmp/candidates.json > /tmp/shortlist.json`.

## 3. Read each JD and rate it
Work on each shortlisted non-signal item, highest `prelim` first, at most 15 per run:
1. Run `python3 jobwatch/fetch.py jd "<url>"`.
   - If the host is blocked (403 from the proxy) or the page is empty, rate from the search snippet. Start `jd_summary` with "JD not read: ".
2. Apply `jobwatch/rate.md` exactly:
   - The match score and its parts, then the bucket: hot (75 or more), watch (55–74), pass (below 55).
   - must_have_gaps, résumé fit (0–10), missing_keywords, and 3 edits that use only verified résumé facts.

For each signal, write why_it_matters, contact and angle, as `rate.md` describes.

## 4. Write to the tracker
1. Send one `ArtifactData batch` of `set` writes to collection `jobs`, doc_id = key. These are new keys only, so no `if_version` is needed, and you never write to an existing key: Ganeysh owns `status` and `notes` there. Split into batches of 50 if needed.
2. Add every rejected key from the shortlist to `meta`/`rejected` with today's date:
   - **Doc already exists:** `update` it with its `if_version`.
   - **Doc doesn't exist:** `set` it.
   - Drop entries older than 90 days.
3. `set` a doc in `runs` with doc_id = today's IST date (YYYY-MM-DD), containing:

   | Field | Value |
   |---|---|
   | `ran_at` | e.g. "2026-11-22 03:05 IST" |
   | `new_roles` | count |
   | `new_signals` | count |
   | `sources_ok` | count |
   | `sources_blocked` | count |
   | `blocked` | names of blocked sources |
   | `notes` | one line, including which résumé source you used |

## 5. Don't commit anything
Make no git commits or pushes. The tracker is the state.

## 6. Final message (sent as the notification)
Keep it to at most 8 lines, plain text:
- `Job Radar <date>: <n> new roles, <m> signals.`
- Up to 3 lines for 🔥 roles: `🔥 <Role> — <Company>, <City> · Match <x> · Fit <y>/10`.
- Up to 2 lines for 📡 signals: `📡 <headline>`.
- If any source was blocked: `Blocked: <names>`.
- Last line: `Open the tracker: https://claude.ai/artifact/To2mfQ9xiNNQa6ETYNccmB`.
