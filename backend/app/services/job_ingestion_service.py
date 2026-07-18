"""
Turns a batch of source-agnostic RawJobPosting objects (from any
JobSource implementation) into rows in the companies/jobs tables,
deduping safely across repeated runs.
"""

import logging

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.job import Job
from app.services.job_sources.base import RawJobPosting

logger = logging.getLogger(__name__)


async def _get_or_create_company(
    db: AsyncSession, source: str, company_token: str, company_name: str
) -> Company:
    """
    Look up a company by (source, source_company_token); create it if
    this is the first time we've seen it. Relies on the unique
    constraint on the Company model to guarantee two concurrent task
    runs can't create duplicate rows for the same company.
    """
    result = await db.execute(
        select(Company).where(
            Company.source == source, Company.source_company_token == company_token
        )
    )
    company = result.scalar_one_or_none()
    if company is not None:
        return company

    company = Company(source=source, source_company_token=company_token, name=company_name)
    db.add(company)
    # flush (not commit) makes company.id available immediately without
    # ending the transaction -- the caller is still batching more work
    # into the same transaction.
    await db.flush()
    return company


async def ingest_job_postings(db: AsyncSession, postings: list[RawJobPosting]) -> dict:
    """
    Upsert a batch of job postings into the database.

    === Dedup strategy, explained ===
    Each Job row is uniquely identified by (source, source_job_id) --
    see the UniqueConstraint on the Job model. This function uses
    Postgres' native `INSERT ... ON CONFLICT DO UPDATE` (SQLAlchemy's
    `pg_insert(...).on_conflict_do_update(...)`) against that
    constraint. In plain terms: "insert this job; if a job with the
    same (source, source_job_id) already exists, update it in place
    instead of erroring or creating a duplicate."

    This is what makes it safe to re-run this same ingestion every 6
    hours (via Celery beat) indefinitely -- postings that haven't
    changed get a harmless no-op update, postings that changed (e.g. a
    title edit) get refreshed, and genuinely new postings get inserted,
    all without ever accumulating duplicate rows.

    An alternative, more naive approach -- "check if it exists, then
    decide to insert or update" -- has a race condition if two task
    runs ever overlap (a check-then-act gap). The single atomic
    upsert statement avoids that entirely.
    """
    companies_seen: dict[str, Company] = {}

    for posting in postings:
        if posting.source_company_token not in companies_seen:
            companies_seen[posting.source_company_token] = await _get_or_create_company(
                db, posting.source, posting.source_company_token, posting.company_name
            )
        company = companies_seen[posting.source_company_token]

        stmt = pg_insert(Job).values(
            company_id=company.id,
            source=posting.source,
            source_job_id=posting.source_job_id,
            title=posting.title,
            location=posting.location,
            department=posting.department,
            description_html=posting.description_html,
            absolute_url=posting.absolute_url,
            source_updated_at=posting.source_updated_at,
            is_active=True,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["source", "source_job_id"],
            set_={
                "title": stmt.excluded.title,
                "location": stmt.excluded.location,
                "department": stmt.excluded.department,
                "description_html": stmt.excluded.description_html,
                "absolute_url": stmt.excluded.absolute_url,
                "source_updated_at": stmt.excluded.source_updated_at,
                "is_active": True,
            },
        )
        await db.execute(stmt)

    await db.commit()

    summary = {
        "companies_processed": len(companies_seen),
        "jobs_processed": len(postings),
    }
    logger.info("Job ingestion summary: %s", summary)
    return summary
