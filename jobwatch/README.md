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
| `seen.json` | Keys seeded from the setup run (the tracker's db is the live record) |

Every fetch goes through the Firecrawl connector, because this cloud environment's network policy blocks direct requests to job sites. LinkedIn is never scraped.
