# Job Radar rating rubric

Apply this to every shortlisted job with bucket `candidate`, `watch` or `also_seen`. Before rating, read the full JD page (firecrawl_scrape, markdown) and the live résumé (Drive doc `1S6F-3CW1YCu2UV2yowj4Xtrzi7F-HIey954Gvpo1MBs`, falling back to `resume_snapshot.md`).

## Step 1: Extract from the JD
- **must_haves:** at most 6, short phrases.
- **nice_to_haves:** at most 4.
- **reports_to**, **team or scope**, **work_mode** (onsite, hybrid or remote), **seniority signals** (years required, people managed, P&L).
- **keywords:** the 10–15 skill and capability terms an ATS or a recruiter would screen for.

## Step 2: Match score, 0–100 (rates the candidate, not the document)

| Part | Max | 0 points | Half points | Full points |
|---|---|---|---|---|
| Seniority and scope | 25 | Below GCD level (ACD, AD, designer) | Lateral (GCD, CD with a bigger remit) | A step up: ECD, Head of Creative, Creative Lead for a platform or brand studio |
| Craft (art background) | 20 | Copy-led, or no craft involved | Craft-agnostic | Art, design or visual-led; design systems; key art |
| Capability overlap | 25 | Little overlap | Some | Integrated campaigns, digital product/UX, generative-AI production, effectiveness, pitching |
| Category and client experience | 15 | None | Adjacent | Direct: FMCG/chocolate, fintech, pharma, hospitality, tech/streaming, real estate, MENA |
| Location and work mode | 15 | Other city, onsite | Other Indian city, hybrid | Mumbai; Bengaluru remote or hybrid; India remote. MENA scores 8 and goes to "Also seen" |

**Buckets:**
- **🔥 Apply now:** score 75 or higher.
- **👀 Watch:** score 55–74.
- **Pass:** below 55. Still write the row so it never repeats, but with bucket `pass`.

**must_have_gaps:** list every must-have the verified résumé can't evidence, honestly. Examples: "8+ yrs people management of 40+ (not stated)", "Copy background preferred".

## Step 3: Résumé fit for this JD, 0–10 (rates the document)

| Part | Max | What it checks |
|---|---|---|
| Keyword coverage | 4 | 4 × (JD keywords found in the résumé ÷ all JD keywords). List the missing keywords. |
| Evidence placement | 3 | Is the strongest proof for each must-have in the top third of page 1? |
| Signal for this reader | 3 | Under Deepali Vyas's framework, would this recruiter see the right signal in 6 seconds (headline, positioning, highlights)? |

## Step 4: Write three tailoring edits
- Each edit must be concrete, use **only facts already in the verified résumé**, and be doable in under 10 minutes.
- **Good:** "Move the PhonePe '70 Crore Names' bullet into Highlights #1 to answer 'large-scale consumer tech'." Or: "Add 'key art' and 'design systems' to Skills (evidenced by the BBH and Sapient work)."
- **Never** suggest adding team size or billings, a relocation line, or any award or metric that isn't in the résumé.

## Step 5: Signals (tier 3)
Signals get no score. Write instead:
- **why_it_matters:** one line, e.g. "ECD (art) exit at Ogilvy Mumbai, so an art-ECD seat is open in your own building".
- **contact:** the role to approach (CCO, NCD, CEO, Head of Talent), and the person's name only if it appears in the article.
- **angle:** a 3-line outreach draft in Ganeysh's voice. It cites one relevant proof point from the résumé and links the Portfolio: https://docs.google.com/presentation/d/1QRsnZ4rm7DlUgCPN3eV9OTFxPZSlNPo_zAnZtLweu5Q/edit?usp=sharing

## Output row (one per job, written to the Job Radar db, collection `jobs`)
```json
{
  "key": "<score.py key>", "company": "", "role": "", "url": "", "sources": ["Workday", "Indeed"],
  "glassdoor": "4.1 ★" , "posted": "2026-10-03", "seen": "2026-10-04", "tier": "1a|1b|2|3",
  "bucket": "hot|watch|also_seen|signal|pass", "group": "network|boutique|tech|consultancy|other",
  "location": "", "work_mode": "", "match": 0, "match_parts": {"seniority":0,"craft":0,"capability":0,"category":0,"location":0},
  "resume_fit": 0.0, "must_have_gaps": [], "missing_keywords": [], "edits": ["", "", ""],
  "jd_summary": "2 lines", "why_it_matters": "", "contact": "", "angle": "",
  "status": "New", "notes": ""
}
```
- **Who owns which fields:** `status` and `notes` belong to Ganeysh. A daily run must never overwrite them on an existing row.
