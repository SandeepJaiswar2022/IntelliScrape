"""
Shared job scraping service.

This is the single implementation of the Greenhouse scrape-and-ingest
pipeline.

It intentionally contains NO Celery code and creates NO database
session of its own.

Whoever calls this function is responsible for supplying an
AsyncSession.

Current callers:

- Celery task
- Admin endpoint

Future callers could include:

- CLI commands
- Scheduled jobs
- Integration tests
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.job_ingestion_service import ingest_job_postings
from app.services.job_sources.greenhouse import GreenhouseJobSource

logger = logging.getLogger(__name__)


async def scrape_greenhouse_jobs(db: AsyncSession) -> dict:
    """
    Fetch every configured Greenhouse board and ingest the returned jobs.

    The caller owns the database session lifecycle.
    """

    source = GreenhouseJobSource(
        company_tokens=settings.greenhouse_company_tokens_list
    )

    postings = await source.fetch_jobs()

    logger.info(
        "Fetched %d job postings from Greenhouse across %d configured companies",
        len(postings),
        len(settings.greenhouse_company_tokens_list),
    )

    summary = await ingest_job_postings(db, postings)

    return summary