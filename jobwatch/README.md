# Job Radar

Each night (02:51 IST) a routine scans for ECD and Head of Creative roles that fit Ganeysh Nayak. It rates each one against his résumé and writes the results to a private tracker page:
https://claude.ai/artifact/To2mfQ9xiNNQa6ETYNccmB

| File | What it is |
|---|---|
| `ROUTINE.md` | The standalone prompt each nightly run follows |
| `sources.yaml` | Company portals, ATS sweep, job boards, Indeed searches, trade-press signal queries |
| `score.py` | First-pass title/location filter, cross-source dedupe, provisional buckets |
| `rate.md` | The JD review rubric: match score (0–100), résumé fit (0–10), tailoring edits |
| `resume_snapshot.md` | Résumé text, used only if the live Google Doc can't be read |
| `fetch.py` | Direct HTTPS fetcher for company portals (Amazon, Netflix, Google, Publicis, Workday tenants), Greenhouse/Lever boards and single JDs |
| `seen.json` | Keys seeded from the setup run (the tracker's db is the live record) |

Since 2026-11-21 the radar needs no connectors. Portals are fetched directly from the "test24 – Job Radar" cloud environment, whose allowed hosts list the portal sites. The ATS sweep, job boards and trade press use the built-in web search. LinkedIn is never scraped. To add a portal, add its host to that environment and an entry to `sources.yaml`.
