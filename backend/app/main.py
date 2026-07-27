"""
Application entrypoint. Run via:
    uvicorn app.main:app --host 0.0.0.0 --port 8000

Responsibilities kept deliberately narrow here:
  - construct the FastAPI app
  - wire cross-cutting middleware (CORS, rate limiting)
  - mount routers
  - expose a health check for load balancers / deploy platforms
No business logic lives in this file.
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from contextlib import asynccontextmanager
from sqlalchemy import text
from app.core.database import engine

from app.api.v1.router import api_router
from app.core.config import settings
from app.utils.rate_limit import limiter

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Checking database connection...")

    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))

    logging.info("Database connected successfully.")

    yield

    logging.info("Closing database engine...")

    await engine.dispose()

app = FastAPI(
    title=settings.APP_NAME,
    description="First milestone: authentication service for IntelliScrape.",
    version="0.1.0",
    # Hide interactive docs in production -- no reason to expose the
    # full API surface/schema to the public once this is live.
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

# --- Rate limiting (see app/utils/rate_limit.py for the storage/scope reasoning) ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- CORS ---
# allow_credentials=True is required for the refresh-token cookie to be
# sent/received cross-origin (frontend on a different domain/port than
# the API, e.g. Vercel <-> Render). Because credentials are allowed,
# allow_origins MUST be an explicit list -- CORS forbids combining
# credentials with a wildcard "*" origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """
    Simple liveness endpoint for deploy platforms (Render/Railway/etc.)
    and uptime monitors. Deliberately does not touch the database --
    a DB-down situation should show up as a failing request elsewhere,
    not as this basic liveness check failing (which platforms may use
    to decide whether to restart the container).
    """
    return {"status": "ok", "environment": settings.ENVIRONMENT}


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Last-resort handler for anything not already caught as an
    HTTPException. Ensures the API never leaks a raw stack trace/500
    HTML page to a client -- especially important once this is
    publicly deployed.
    """
    logging.getLogger(__name__).exception("Unhandled exception on %s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again."},
    )
