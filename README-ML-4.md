# IntelliScrape — Milestones 1–4

**Milestone 1**: FastAPI authentication service (JWT + rotating refresh tokens).
**Milestone 2**: A Celery task pulling job postings from Greenhouse's public API for 5 companies, deduped in Postgres.
**Milestone 3**: A `GET /api/v1/jobs` search/filter API, plus a React + TypeScript + Tailwind frontend listing the scraped jobs.
**Milestone 4** (this update): Job detail pages, plain-text description previews, and two new derived filters — experience level and tech stack — extracted from job text via rule-based keyword matching (no LLM).

---

## What's new in Milestone 4

### Backend
- **Rule-based extraction pipeline**: every job gets `experience_level` and `tech_stack` populated automatically at ingestion time (not at query time), via keyword matching against the title/description. See `app/core/tech_taxonomy.py` for the full taxonomy and `app/services/job_extraction_service.py` for the matching logic — both are heavily commented on *why* rule-based (vs. LLM) was chosen and its known precision/recall limits.
- **`GET /api/v1/jobs/{id}`** — full job detail, including the untruncated plain-text description. This is the stable, linkable resource the frontend's detail page points to, and — per your note — the intended foundation for later features that need to reference one specific posting (e.g. resume matching against this exact job).
- **`GET /api/v1/jobs/tech-stack-options`** — the full canonical tag list, powering the frontend's autocomplete.
- **`GET /api/v1/jobs`** extended with `experience_level` and `tech_stack` (repeatable) query params.
- **HTML → plain text conversion** via BeautifulSoup (`app/utils/html_text.py`) — used both to clean text before tech-stack keyword matching, and to safely render descriptions in API responses without ever needing `dangerouslySetInnerHTML` on the frontend (a deliberate simplification — see the file's docstring).

### Frontend
- **`/jobs/:jobId`** route — a real, linkable detail page (added `react-router-dom`).
- Job cards now show a **description preview** (2-line clamp), **tech-stack chips**, an **experience-level badge**, and a distinct **"Apply"** button separate from the internal "View full details" link (a card can't nest two different links, so these had to be pulled apart from the single big clickable card in Milestone 3).
- **Experience level filter** — plain dropdown, fixed buckets.
- **Tech stack filter** — searchable autocomplete with removable chips, built from scratch (`TechStackAutocomplete.tsx`), matching your choice from our planning discussion.

---

## Known, deliberate limitations (read before extending this)

- **Rule-based extraction is not perfect.** A posting that says "5+ years of distributed systems experience" without the word "Senior" won't get an experience level. A skill phrased unusually, or not in the taxonomy, won't get tagged. This was a conscious MVP tradeoff over LLM-based extraction — see the taxonomy module's docstring for the full reasoning. Upgrade path if this becomes the bottleneck: swap `job_extraction_service.py`'s internals for an LLM call; its function signatures wouldn't need to change for callers.
- **"Manager" matches the "Lead" bucket broadly** — a title like "Product Manager" gets tagged "Lead" purely because it contains "manager", even though it isn't an engineering seniority level in the usual sense. Known, not a bug — flagged during testing, not silently swept under the rug.
- **Rich formatting is not preserved** in descriptions — bold text, links, and bullet structure from the original Greenhouse posting are stripped down to plain text. This was a deliberate simplification to avoid needing an HTML sanitization library + `dangerouslySetInnerHTML` on the frontend. Worth revisiting only if losing that formatting turns out to matter.

---

## New/changed backend files this milestone

```
NEW:      backend/app/core/tech_taxonomy.py
NEW:      backend/app/utils/html_text.py
NEW:      backend/app/utils/__init__.py            (only if not already present from Milestone 1)
NEW:      backend/app/services/job_extraction_service.py
NEW:      backend/alembic/versions/6cdcceae8480_add_experience_level_and_tech_stack_to_.py
MODIFIED: backend/app/models/job.py                 (added experience_level, tech_stack columns)
MODIFIED: backend/app/services/job_ingestion_service.py  (calls extraction during upsert)
MODIFIED: backend/app/schemas/job.py                (new fields, JobDetailResponse)
MODIFIED: backend/app/services/job_query_service.py (new filters, get_job_by_id)
MODIFIED: backend/app/api/v1/endpoints/jobs.py      (new endpoints, route ordering matters -- see file)
MODIFIED: backend/requirements.txt                  (added beautifulsoup4)
```

## New/changed frontend files this milestone

```
NEW:      frontend/src/pages/JobDetailPage.tsx
NEW:      frontend/src/hooks/useJob.ts
NEW:      frontend/src/hooks/useTechStackOptions.ts
NEW:      frontend/src/components/ExperienceLevelSelect.tsx
NEW:      frontend/src/components/TechStackAutocomplete.tsx
MODIFIED: frontend/src/types/job.ts                 (new fields, JobDetail, EXPERIENCE_LEVELS)
MODIFIED: frontend/src/lib/api.ts                   (fetchJobById, fetchTechStackOptions, extended fetchJobs)
MODIFIED: frontend/src/hooks/useJobs.ts              (comment cleanup only, no logic change)
MODIFIED: frontend/src/components/JobFiltersBar.tsx  (new filter props/UI)
MODIFIED: frontend/src/components/JobCard.tsx        (restructured -- see below)
MODIFIED: frontend/src/pages/JobsPage.tsx            (new filter state)
MODIFIED: frontend/src/App.tsx                       (added routing)
MODIFIED: frontend/src/main.tsx                      (wrapped in BrowserRouter)
MODIFIED: frontend/package.json                      (added react-router-dom)
```

**Why `JobCard.tsx` changed shape**: in Milestone 3 the whole card was one big `<a>` linking straight to Greenhouse. Now that there's both an internal detail-page link AND an external apply link, they can't be nested inside each other — the card became a `<div>` wrapper with the title/company area as an internal `<Link>`, and a visually distinct "Apply" button as the external link.

---

## Running it

### 1. Backend

```bash
cp .env.example .env   # if you haven't already; no NEW variables needed this milestone
docker compose up --build
docker compose exec backend alembic upgrade head
```

Two migrations will apply in order (Milestone 3's tables, then this milestone's new columns) if you're starting fresh. If you already ran Milestone 3's migration, only the new one applies.

**Re-tag existing jobs**: if you already have jobs in your database from before this milestone, they won't have `experience_level`/`tech_stack` populated until they're re-scraped (the extraction runs at ingestion time, not retroactively). Trigger a fresh fetch to backfill them:
```bash
docker compose exec celery_worker celery -A app.core.celery_app call app.tasks.job_scraping_tasks.fetch_greenhouse_jobs

docker compose logs -f celery_worker
```

### 2. Frontend

```bash
cd frontend
cp .env.example .env   # if you haven't already
npm install             # picks up the new react-router-dom dependency
npm run dev
```

Open **http://localhost:5173**. Try the experience-level dropdown and the tech-stack autocomplete (type "python" or "react" to see suggestions), and click a job title to see the new detail page.

---

## Verifying it worked

```bash
# Tech stack options list
curl "http://localhost:8000/api/v1/jobs/tech-stack-options"

# Filter by experience level
curl "http://localhost:8000/api/v1/jobs?experience_level=Senior"

# Filter by tech stack (OR semantics -- matches jobs with ANY of these tags)
curl "http://localhost:8000/api/v1/jobs?tech_stack=Python&tech_stack=React"

# Fetch a single job's full detail (grab a real id from the list response first)
curl "http://localhost:8000/api/v1/jobs/<job-id-here>"
```

In the DB directly:
```sql
SELECT title, experience_level, tech_stack FROM jobs LIMIT 10;
```

---

## Next steps

Per our planning discussion: deploy Milestones 1–4 together as the first live MVP (Render + Supabase + Vercel). The multi-ATS router (Lever/Ashby/SmartRecruiters as additional `JobSource` implementations, Playwright as a last-resort fallback for whatever's left) is the deliberately deferred next milestone after that.
