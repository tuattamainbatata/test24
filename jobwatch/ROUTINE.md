# Job Radar: nightly run (standalone instructions)

You are running Ganeysh Nayak's nightly Job Radar. Ganeysh is a Group Creative Director at Ogilvy Mumbai, art-led, aiming for ECD or Head of Creative.

Work through the steps below in order. Finish with a short summary, which becomes the push/email notification.

- **Tracker page:** https://claude.ai/artifact/To2mfQ9xiNNQa6ETYNccmB. It has a `db` with collections `jobs`, `runs` and `meta`.
- **Repo folder:** `jobwatch/` in this repository. If it's missing, check out branch `claude/resume-career-progression-j9wclz`: `git fetch origin claude/resume-career-progression-j9wclz && git checkout claude/resume-career-progression-j9wclz`.
- **Connectors:** Firecrawl, Google Drive, Indeed. Load their tools with ToolSearch. Load `ArtifactData` the same way.
- **Network:** this environment blocks direct HTTP to job sites. Fetch everything through Firecrawl; never curl a portal.

## 0. Load what you need
1. Read `jobwatch/sources.yaml`, `jobwatch/rate.md` and `jobwatch/score.py --help`.
2. Read the live résumé with Google Drive `read_file_content`, fileId `1S6F-3CW1YCu2UV2yowj4Xtrzi7F-HIey954Gvpo1MBs`. If that fails, use `jobwatch/resume_snapshot.md`.
3. Build the dedupe list from the tracker, since the tracker is the source of truth:
   - `ArtifactData list` on collection `jobs`. Page through every result: each doc id is a key already seen.
   - `ArtifactData get` on `meta`/`rejected`, which holds `{"keys": {key: date}}`. It may not exist yet.
   - Write the combined keys to `jobwatch/seen.json` as `{"keys": {key: {...}}}`, so `score.py` skips them.

## 1. Collect candidates (date window: the last 24 hours)
Collect every hit into `candidates.json` in your scratchpad. Each entry is a list item shaped `{company, title, location, url, source, posted, tier, snippet, group}`, where `group` is network | boutique | tech | consultancy | other.

- **Tier 1a, company portals:** for each portal in `sources.yaml`, and each query in `portal_queries`, call `firecrawl_scrape` on the URL with `formats: ["json"]`, the `jobs_schema` from the YAML, `maxAge: 0`, and a prompt to list every job result.
  - Amazon and Netflix return JSON APIs. The JSON format extracts them fine.
  - If a portal returns zero jobs for every query on a page that normally lists jobs, run a fallback search: `firecrawl_search` with `site:<portal host> <query> India`, `tbs: "qdr:d"`.
  - Count a portal as "blocked" only if both attempts fail.
- **Tier 1b, ATS sweep:** run `firecrawl_search` (`sources: ["web"]`, `tbs: "qdr:d"`, `limit: 20`) once for each `ats_domains` entry, using `ats_query`. Take company and title from the result title and URL.
- **Tier 2, job boards:**
  - Run each `board_queries` entry as `firecrawl_search` with `tbs: "qdr:d"`.
  - Run each `indeed_searches` entry with the Indeed connector `search_jobs` (`country_code: "IN"`). Keep only results posted in the last 3 days.
  - For Glassdoor results, use them to find roles and to capture the company rating (e.g. "3.4 ★"). Don't crawl Glassdoor pages. Look for the same role on the company's own portal and prefer that link.
  - For each named boutique in `sources.yaml`, run one combined search, `("<name>" hiring creative)`, with `tbs: "qdr:w"`.
- **Tier 3, trade-press signals:** run each `signal_queries` entry as `firecrawl_search`, `tbs: "qdr:d"`, `limit: 15`.
  - Keep only India or MENA creative-leadership moves, account wins and office openings that could open a seat suited to Ganeysh.
  - Set the title to a one-line headline, the tier to "3", and the company to the agency where a seat may open.
- **Never** scrape LinkedIn.
- **Firecrawl limits:** if Firecrawl returns 429 or "concurrency limited", run calls one at a time and wait about 10 seconds before retrying, at most twice. Never use Bash `sleep` longer than 30 seconds.

## 2. Filter and dedupe
Run `python3 jobwatch/score.py filter candidates.json > shortlist.json`. It drops roles already seen, rejects wrong titles and locations, merges one role found in several places, and sets a provisional bucket (`candidate`, `watch`, `also_seen` or `signal`).

## 3. Read each JD and rate it
Work on each shortlisted non-signal item, highest `prelim` first, at most 15 per night:
1. Call `firecrawl_scrape` on its URL with `formats: ["json"]` and a schema `{title, company, location, work_mode, posted, reports_to, must_haves[], nice_to_haves[], years_required, keywords[], summary}`. Don't use markdown; Workday pages repeat the JD in their metadata.
2. Apply `jobwatch/rate.md` exactly:
   - Match score and its parts, then the bucket: hot (75 or more), watch (55–74), pass (below 55).
   - must_have_gaps, résumé fit (0–10), missing_keywords, and 3 edits that use only verified résumé facts.
3. Build one row per role in the format `rate.md` shows.

For each signal: write why_it_matters, contact and angle, as `rate.md` describes.

## 4. Write to the tracker
1. Send a single `ArtifactData batch` of `set` writes to collection `jobs`, doc_id = key. These are new keys only, so no `if_version` is needed. Never write to an existing key, because Ganeysh owns `status` and `notes` there. Split into batches of 50 if there are more.
2. Add every rejected key from `shortlist.json` to `meta`/`rejected`:
   - **Doc already exists:** `update` it with the `if_version` you read.
   - **Doc doesn't exist:** `set` it.
   - Remove entries older than 90 days.
3. `set` a doc in `runs` with doc_id = today's IST date (YYYY-MM-DD), containing:

   | Field | Value |
   |---|---|
   | `ran_at` | e.g. "2026-10-05 03:04 IST" |
   | `new_roles` | count |
   | `new_signals` | count |
   | `sources_ok` | count |
   | `sources_blocked` | count |
   | `blocked` | names of blocked sources |
   | `notes` | one line |

**Fallback:** if `ArtifactData` isn't available or fails twice, create a Google Doc instead. Title it "Job Radar — YYYY-MM-DD" and put it in Drive folder `11vpJy_4YEpyCRrObITgHUmMEVxDgK_7k`. Upload HTML with fonts Hepta Slab (headings) and Syne (body), and the same fields per role. Say in the summary that the tracker write failed.

## 5. Don't commit anything
The tracker's db is the state, so make no git commits or pushes. `seen.json` is a local working file.

## 6. Final message (sent as the notification)
Keep it to at most 8 lines, plain text:
- `Job Radar <date>: <n> new roles, <m> signals.`
- Up to 3 lines for 🔥 roles: `🔥 <Role> — <Company>, <City> · Match <x> · Fit <y>/10`.
- Up to 2 lines for 📡 signals: `📡 <headline>`.
- If any source was blocked: `Blocked: <names>`.
- Last line: `Open the tracker: https://claude.ai/artifact/To2mfQ9xiNNQa6ETYNccmB`.

If there is nothing new, say so in one line and still include the link.
