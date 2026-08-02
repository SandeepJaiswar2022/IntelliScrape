"""
Celery tasks for pulling job postings from external sources into the
database. If Celery is new to you, read the module docstring in
app/core/celery_app.py first -- it explains the broker/worker/beat
concepts this file relies on.
"""

import asyncio
import logging

from app.core.celery_app import celery_app
from app.core.database import task_db_session
from backend.app.services.job_scraping_service import scrape_greenhouse_jobs

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.tasks.job_scraping_tasks.fetch_greenhouse_jobs",
    # If this task raises any exception (a Greenhouse timeout, a
    # transient DB connection blip, etc.), Celery retries it
    # automatically instead of the failure just sitting there until
    # someone notices. `retry_backoff=True` waits longer between each
    # retry (roughly 1s, 2s, 4s...) instead of hammering immediately;
    # `retry_backoff_max` caps that wait at 5 minutes;
    # `max_retries: 3` gives up after 3 attempts rather than retrying
    # forever.
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_kwargs={"max_retries": 3},
)
def fetch_greenhouse_jobs() -> dict:
    """
    The function Celery actually invokes (via `celery beat` on a
    schedule, or manually -- see README for how to trigger it by hand).

    Celery tasks are plain SYNCHRONOUS functions -- the worker calls
    this like any normal Python function, with no `await` involved.
    But our database layer and HTTP client (httpx) are async. The
    standard bridge for that mismatch is `asyncio.run(...)`: it starts
    a fresh event loop, runs the async code to completion, and returns
    the plain result -- so from Celery's point of view, this still
    looks like an ordinary sync function that returns a dict.
    """
    return asyncio.run(_fetch_greenhouse_jobs_async())


async def _fetch_greenhouse_jobs_async() -> dict:
    async with task_db_session() as db:
        return await scrape_greenhouse_jobs(db)
