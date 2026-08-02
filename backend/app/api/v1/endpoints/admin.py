"""
Admin-only endpoints.

=== Why this endpoint exists ===
Render's free tier has no background worker, so Celery beat/worker
can't run in that environment at all -- there's no process to pick up
scheduled or manually-queued tasks. This endpoint is a second entry
point into the exact same scraping work, reachable over plain HTTP
(which the free web-service tier DOES support), for use until a paid
tier with a real background worker is in place.

This file contains ZERO scraping logic of its own. It depends on
`require_admin` for authorization and calls straight into
`scrape_greenhouse_jobs` (the single shared implementation -- see
app/services/job_scraping_service.py). If you're looking for the
actual scrape-and-ingest logic, it is not here and it is not supposed
to be here.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import require_admin
from app.models.user import User
from app.services.job_scraping_service import scrape_greenhouse_jobs

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/scrape")
async def trigger_scrape(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
) -> dict:
    """
    Manually trigger a full Greenhouse scrape-and-ingest run,
    synchronously, within this request.

    Note the "synchronously" -- unlike the Celery path, this blocks
    the request until the scrape finishes (making several HTTP calls
    to Greenhouse, one per configured company, then writing to
    Postgres). For today's company list (a handful) this completes
    in a few seconds and is a perfectly reasonable trade-off for a
    manual "click a button to refresh" admin action. It would NOT be
    reasonable to call this from a scheduled/high-frequency path, or
    once the company list grows large enough that the run takes long
    enough to risk an HTTP timeout -- that's exactly the scenario the
    Celery path (background, retryable, no request waiting on it) is
    for, and why this milestone deliberately keeps Celery rather than
    replacing it with this endpoint.

    Uses the standard `get_db` request-scoped session (NOT
    `task_db_session`, which exists specifically to work around
    Celery's process-forking model -- a plain FastAPI request has no
    such concern, so the app's normal shared connection pool is the
    right choice here).
    """
    summary = await scrape_greenhouse_jobs(db)
    return summary