# IntelliScrape — Milestones 1 & 2 (Auth + Job Scraping)

**Milestone 1** is a standalone FastAPI authentication service.
**Milestone 2** (this update) adds the first real data pipeline: a
Celery task that pulls job postings from Greenhouse's public API for a
configurable list of companies (starting with 5, built to scale to 20+
with zero code changes) and stores them in Postgres, deduped across
repeated runs.

## What is Celery, and why does this project need it?

If you've never used Celery before, here's the short version (the full
explanation, with more detail, lives in
`backend/app/core/celery_app.py` — read that file's docstring when you
get to it).

FastAPI is built for **request/response**: someone hits an endpoint,
your code runs for a few milliseconds, a response goes back. That
model doesn't fit "fetch job postings from 5 (soon 20+) external
companies' APIs" — that can take several seconds, can fail partway
through, and critically, needs to happen **whether or not anyone is
using the app right now** (e.g. "every 6 hours, automatically").

Celery moves that kind of work into its own separate processes,
outside the request/response cycle entirely:

- **Redis** acts as a simple mailbox/queue: "please run this task" gets
  dropped onto it.
- A **`celery worker`** process is constantly watching that queue. When
  a task shows up, it picks it up and actually runs the Python function.
- A **`celery beat`** process is a scheduler — it doesn't do any work
  itself, it just drops tasks onto the queue on a timer (our "every 6
  hours" rule). It's a separate process from the worker on purpose.

None of this runs inside your FastAPI process. Look at
`docker-compose.yml` — `celery_worker` and `celery_beat` are their own
containers, completely independent of the `backend` container serving
HTTP traffic. That separation is the whole point: if Greenhouse is slow
or down, your API stays fast and responsive regardless.

## Companies configured (start of 5)

Verified, real Greenhouse board tokens (the slug in a company's public
careers URL — e.g. `job-boards.greenhouse.io/stripe` → token `stripe`):

```
stripe, gitlab, figma, robinhood, asana
```

Configured via `GREENHOUSE_COMPANY_TOKENS` in `.env` — a plain
comma-separated list. Growing this to 20+ later is a one-line `.env`
change, no code changes.

## New pieces added this milestone

```
backend/app/
├── core/
│   └── celery_app.py           # Celery app instance, config, beat schedule
├── models/
│   ├── company.py               # Company table
│   └── job.py                   # Job table (unique constraint = the dedup mechanism)
├── services/
│   ├── job_sources/
│   │   ├── base.py              # JobSource interface + RawJobPosting shape
│   │   └── greenhouse.py        # Greenhouse API implementation
│   └── job_ingestion_service.py # Upserts RawJobPosting -> DB rows, dedup logic
└── tasks/
    └── job_scraping_tasks.py    # The actual Celery task
```

**Why the `JobSource` abstraction exists**: per this project's roadmap,
scraping LinkedIn/Naukri directly is legally risky (ToS violations) and
technically fragile (anti-bot defenses). Greenhouse's public API is the
safe starting point. But the whole design is built so that adding a
second source later (Lever's API, a specific company's own career page)
never touches `job_ingestion_service.py` or the Celery task — only a
new class implementing `JobSource.fetch_jobs()`.

## How the dedup actually works

Every `Job` row is uniquely identified by `(source, source_job_id)` —
see the `UniqueConstraint` on the `Job` model. Ingestion uses Postgres'
native `INSERT ... ON CONFLICT DO UPDATE`: re-running the fetch (every
6 hours, or manually) updates existing postings in place instead of
creating duplicates. This was verified directly against a real
Postgres instance during development — see the git history / build
notes if you want the exact test, but in short: running the same
ingestion twice with one changed job, one unchanged job, and one new
job resulted in exactly 3 rows, not 4, with the changed job's title
correctly updated in place.

## Running it locally

## What's implemented

- User registration (email + password + full name)
- Login with JWT access tokens + rotating opaque refresh tokens
- Refresh token stored as an HttpOnly cookie (never touchable by
  client-side JS)
- Logout (single session) and logout-all (every session/device)
- Forgot-password / reset-password flow (token generated and logged;
  real email delivery is a follow-up — see below)
- Per-account brute-force lockout + per-IP rate limiting
- `GET /me` — protected route returning the current user

## What's deliberately NOT implemented yet

- Email verification enforcement (the `is_verified` column exists, but
  nothing blocks login on it yet — needs a real email provider first)
- Real email sending for password reset (currently just logged to
  console — see the `TODO` comment in
  `app/api/v1/endpoints/auth.py::forgot_password`)
- Anything related to jobs, companies, scraping, Celery, or Redis —
  that's the next milestone, and this docker-compose file is
  intentionally lean so this milestone stays easy to reason about on
  its own

## Project structure

```
intelliscrape/
├── docker-compose.yml       # postgres + backend for local dev
├── .env.example             # copy to .env and fill in secrets
└── backend/
    ├── Dockerfile
    ├── requirements.txt
    ├── alembic.ini           # migration config
    ├── alembic/
    │   ├── env.py            # wired to app settings + models
    │   └── versions/         # migration files land here
    └── app/
        ├── main.py            # FastAPI app, CORS, rate limiter, health check
        ├── core/
        │   ├── config.py      # all environment/config in one place
        │   ├── database.py    # async engine/session, Base, get_db dependency
        │   └── security.py    # password hashing, JWT, refresh token crypto
        ├── models/
        │   ├── user.py        # User table
        │   └── refresh_token.py  # RefreshToken table (session tracking)
        ├── schemas/
        │   └── auth.py        # request/response validation (Pydantic)
        ├── services/
        │   └── auth_service.py  # all auth business logic lives here
        ├── dependencies/
        │   └── auth.py        # get_current_user / get_current_active_user
        ├── api/v1/
        │   ├── router.py      # aggregates all v1 routers
        │   └── endpoints/
        │       └── auth.py    # HTTP layer: routes, cookies, status codes
        └── utils/
            └── rate_limit.py  # slowapi limiter shared across endpoints
```

## Running it locally

```bash
cp .env.example .env
# Edit .env: at minimum, set a real JWT_SECRET_KEY
# (generate one with: openssl rand -hex 32)

docker compose up --build
```

The API will be live at `http://localhost:8000`.
Interactive docs (dev only): `http://localhost:8000/docs`.

This now brings up 5 containers: `postgres`, `backend`, `redis`,
`celery_worker`, `celery_beat`. Check all of them came up healthy with
`docker compose ps`.

### First-time database setup (migrations)

A migration covering all four tables (`users`, `refresh_tokens`,
`companies`, `jobs`) is already included in
`alembic/versions/` — it was generated and applied against a real
Postgres instance during development to confirm it's correct, so you
don't need to regenerate it. Just apply it:

```bash
docker compose exec backend alembic upgrade head
```

From now on, whenever you change a model in `app/models/` (adding a
field, a new table, etc.), generate a new migration the same way:

```bash
docker compose exec backend alembic revision --autogenerate -m "describe your change"
docker compose exec backend alembic upgrade head
```

### Manually triggering the Greenhouse fetch (without waiting for the schedule)

The task runs automatically every 6 hours via `celery_beat`, but for
testing you don't want to wait. Trigger it directly:

```bash
docker compose exec celery_worker celery -A app.core.celery_app call app.tasks.job_scraping_tasks.fetch_greenhouse_jobs
```

Then watch the `celery_worker` logs (`docker compose logs -f
celery_worker`) to see it fetch and ingest. Verify the results landed
in the database:

```bash
docker compose exec postgres psql -U intelliscrape -d intelliscrape_db -c "SELECT title, location FROM jobs LIMIT 10;"
docker compose exec postgres psql -U intelliscrape -d intelliscrape_db -c "SELECT name, source_company_token FROM companies;"
```

Run the same trigger command a second time — row counts in `jobs`
should NOT roughly double; they should stay the same (existing postings
updated in place) plus only genuinely new postings added.

## Trying the endpoints

```bash
# Register (also logs you in — response includes an access_token)
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{"email":"you@example.com","password":"StrongPass1!","full_name":"Your Name"}'

# Call a protected route with the access_token from the response above
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token_here>"

# Refresh (uses the cookie jar saved above)
curl -X POST http://localhost:8000/api/v1/auth/refresh -b cookies.txt -c cookies.txt

# Logout
curl -X POST http://localhost:8000/api/v1/auth/logout -b cookies.txt
```

## Auth edge cases this milestone handles (and why)

| Edge case | Handling |
|---|---|
| Duplicate registration with different email casing | Email normalized to lowercase before uniqueness check and storage |
| Weak password | Rejected at the schema layer: min 8 chars, upper+lower+digit+special char required |
| Wrong password vs. unknown email | Both return an identical 401 message — prevents attacker from learning which emails are registered |
| Timing-based user enumeration | A dummy password hash verification runs even when the email isn't found, so response time doesn't leak whether the account exists |
| Repeated failed logins on one account | Account locks for a configurable window after N failed attempts (per-account) |
| Credential stuffing across many accounts from one source | Separate IP-based rate limit on register/login/forgot-password (per-IP) |
| Stolen/leaked refresh token replayed after rotation | Reuse of an already-rotated token revokes *every* active session for that user (fail-safe) |
| Password reset requested for non-existent email | Same generic response either way — no enumeration via this endpoint either |
| Password reset completed | All existing sessions are revoked — forces re-login everywhere, including any device an attacker may have had access to |
| Account deactivated mid-session | Checked on every request via `get_current_active_user`, not just at login |
| Expired vs. tampered access token | Distinguished internally (different exceptions) so the frontend could show "please wait, refreshing" vs. "please log in again" if desired |
| XSS stealing the refresh token | Impossible by construction — refresh token is HttpOnly, never exposed to JS, never in a JSON body |
| CSRF via the refresh cookie | `SameSite=Lax` on the cookie blocks cross-site POST requests from third-party pages from being able to trigger a refresh/logout using the victim's cookie |

## Deploying (this milestone)

Per the project roadmap, this milestone is small enough to deploy
immediately for real feedback:

- **Backend**: Render or Railway (Docker deploy from this `backend/`
  directory). Set all `.env.example` variables as environment variables
  in the platform's dashboard — **never commit real secrets**.
- **Database**: Supabase or the platform's managed Postgres. Update
  `DATABASE_URL` accordingly (Supabase gives you a ready-made
  `postgresql+asyncpg://...` style string — just confirm the driver
  prefix matches, since some dashboards show the plain `postgresql://`
  form meant for sync drivers).
- Set `COOKIE_SECURE=true` and `ENVIRONMENT=production` once served
  over HTTPS — cookies without `Secure` should never leave local dev.
- Set `CORS_ORIGINS` to your actual deployed frontend URL(s) once the
  frontend milestone exists.

## Next milestone

Per the roadmap: Phase 2 — a search/browse API (`GET /api/v1/jobs` with
filters for role/location/tech stack) plus a React frontend page to
list the scraped jobs. This milestone deliberately has no jobs-facing
API endpoints yet — just the pipeline getting real data into Postgres
reliably, which everything else depends on.
