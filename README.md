# IntelliScrape — Milestones 1–3

**Milestone 1**: FastAPI authentication service (JWT + rotating refresh tokens).
**Milestone 2**: A Celery task pulling job postings from Greenhouse's public API for 5 companies, deduped in Postgres.
**Milestone 3** (this update): A `GET /api/v1/jobs` search/filter API, plus a standalone React + TypeScript + Tailwind frontend that lists the scraped jobs.

## Project structure

```
intelliscrape/
├── docker-compose.yml       # postgres + backend + redis + celery_worker + celery_beat
├── .env.example             # backend env vars — copy to .env
└── backend/
    └── app/
        ├── main.py
        ├── core/                  # config, database, security, celery_app
        ├── models/                # User, RefreshToken, Company, Job
        ├── schemas/               # auth.py, job.py
        ├── services/              # auth_service, job_ingestion_service, job_query_service, job_sources/
        ├── api/v1/endpoints/      # auth.py, jobs.py
        └── tasks/                 # job_scraping_tasks.py

frontend/                    # separate project, run independently of docker-compose
├── .env.example             # VITE_API_BASE_URL — copy to .env
└── src/
    ├── main.tsx, App.tsx
    ├── pages/JobsPage.tsx        # the single page for this milestone
    ├── components/               # Navbar, JobCard, JobFiltersBar, Pagination, etc.
    ├── hooks/                    # useJobs (TanStack Query), useDebouncedValue
    ├── context/ThemeContext.tsx  # dark/light mode, persisted to localStorage
    ├── lib/                      # api.ts (fetch client), freshness.ts (signal-bar logic)
    └── types/job.ts              # mirrors the backend's job schema
```

## Design notes (frontend)

The visual direction is "market signal" — this is a job-intelligence
product, so the design leans into data density and fast scanning
rather than a marketing-site hero. Three-role type system: **Space
Grotesk** (headings), **Inter** (body), **IBM Plex Mono** (tags,
locations, timestamps — ties the UI's data feel together). Single
accent color ("signal amber"). The signature element: each job card's
left edge is a vertical bar whose color intensity encodes how recently
the posting was updated — bright amber for postings updated in the
last 3 days, fading for older ones. This is functional (fastest way to
scan "what's new"), not decorative.

Full rationale is documented in `frontend/src/index.css` and
`frontend/src/lib/freshness.ts`.

## Running the backend (Docker)

```bash
cp .env.example .env
# set JWT_SECRET_KEY (openssl rand -hex 32) if you haven't already

docker compose up --build
docker compose exec backend alembic upgrade head
```

Trigger the Greenhouse fetch manually to get real data in before trying the frontend:
```bash
docker compose exec celery_worker celery -A app.core.celery_app call app.tasks.job_scraping_tasks.fetch_greenhouse_jobs
```

Confirm the new endpoint works:
```bash
curl "http://localhost:8000/api/v1/jobs"
curl "http://localhost:8000/api/v1/jobs?title=engineer&location=remote"
```

## Running the frontend (separately, not in Docker)

The frontend is a standalone Vite project — it talks to the backend
over HTTP, so it doesn't need to be containerized alongside it for
local development.

```bash
cd frontend
cp .env.example .env
# defaults to http://localhost:8000, matching the Docker backend above — only change if needed

npm install
npm run dev
```

Open **http://localhost:5173**. You should see the job listing page,
pulling real data from your running backend.

If you see a CORS error in the browser console: your backend's
`CORS_ORIGINS` (in the root `.env`) needs to include
`http://localhost:5173` — it does by default in `.env.example`, so
this only happens if you changed it.

### Building for production

```bash
cd frontend
npm run build
```
Output lands in `frontend/dist/` — a fully static site, deployable to
Vercel/Netlify/any static host. Remember to set `VITE_API_BASE_URL` to
your deployed backend's URL as an environment variable on whichever
platform you use (Vite bakes this in at build time, not runtime).

## New/changed backend files this milestone

```
NEW:      backend/app/schemas/job.py
NEW:      backend/app/services/job_query_service.py
NEW:      backend/app/api/v1/endpoints/jobs.py
MODIFIED: backend/app/api/v1/router.py   (registers the new jobs router)
```

## API reference: GET /api/v1/jobs

| Query param | Type | Description |
|---|---|---|
| `title` | string, optional | Case-insensitive partial match on job title |
| `location` | string, optional | Case-insensitive partial match on location |
| `company` | string, optional | Case-insensitive partial match on company name (not yet exposed in the frontend UI, but available) |
| `page` | int, default 1 | 1-indexed page number |
| `page_size` | int, default 20, max 100 | Results per page |

Response shape:
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "Senior Backend Engineer",
      "company_name": "Stripe",
      "location": "Remote - US",
      "department": "Engineering",
      "absolute_url": "https://job-boards.greenhouse.io/stripe/jobs/201",
      "source_updated_at": "2026-06-01T00:00:00Z",
      "scraped_at": "2026-07-18T10:25:35.721249Z"
    }
  ],
  "total": 4,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

Deliberately not implemented yet: a `tech_stack` filter (mentioned in
the original roadmap) — the `jobs` table has no `tech_stack` column
yet, since nothing in the Greenhouse ingestion pipeline extracts one.
That's a schema + ingestion change for a later milestone, not just an
endpoint change.

## Next milestone

Per the roadmap: authentication pages on the frontend (register/login
forms wired to the Milestone 1 auth API, protected routes, silent
token refresh) — deliberately deferred until the core browsing
experience worked end-to-end first.
