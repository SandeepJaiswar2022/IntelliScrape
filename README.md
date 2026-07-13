# IntelliScrape — First Milestone (Auth Service)

This is the first buildable slice of IntelliScrape: a standalone
FastAPI authentication service. Nothing job/scraping-related lives
here yet — that's the next milestone. This milestone is deliberately
scoped to **just** getting auth right, since everything else in the
product depends on it.

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

### First-time database setup (migrations)

With the containers running, generate and apply the initial migration:

```bash
docker compose exec backend alembic revision --autogenerate -m "create users and refresh_tokens tables"
docker compose exec backend alembic upgrade head
```

From then on, whenever you change a model in `app/models/`, repeat the
same two commands to generate and apply a new migration.

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

Frontend (React) auth pages (register/login forms, protected route
handling, silent token refresh) — nothing job-related yet, per the
roadmap's ordering: get the whole auth loop working end-to-end,
frontend included, before adding any scraping/jobs functionality.
