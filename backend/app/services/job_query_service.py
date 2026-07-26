"""
Job listing/search/detail query logic, kept separate from the HTTP
layer (app/api/v1/endpoints/jobs.py) -- same pattern as auth_service.py:
the endpoint stays thin, the actual query-building logic lives here
where it's independently readable and testable.
"""

import math
import uuid

from sqlalchemy import or_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.company import Company
from app.models.job import Job


async def list_jobs(
    db: AsyncSession,
    title: str | None,
    location: str | None,
    company: str | None,
    experience_level: str | None,
    tech_stack: list[str] | None,
    page: int,
    page_size: int,
) -> tuple[list[Job], int]:
    """
    Return (jobs_for_this_page, total_matching_count) for the given
    filters. Filters are optional and combine with AND when more than
    one is provided.

    `title`/`location`/`company` use case-insensitive partial matching
    (`ilike`) -- "engineer" should match "Senior Software Engineer".
    `experience_level` is an exact match against the derived bucket
    column. `tech_stack` matches if the job has ANY of the requested
    tags (OR semantics, not AND) -- see the reasoning below.
    """
    base_query = select(Job).where(Job.is_active.is_(True))

    if title:
        base_query = base_query.where(Job.title.ilike(f"%{title}%"))
    if location:
        base_query = base_query.where(Job.location.ilike(f"%{location}%"))
    if company:
        # `.has(...)` filters on the related Company row via a subquery
        # rather than an explicit JOIN -- this avoids interfering with
        # the `joinedload` used below to eager-load company data for
        # display, which uses its own LEFT OUTER JOIN under the hood.
        base_query = base_query.where(Job.company.has(Company.name.ilike(f"%{company}%")))
    if experience_level:
        base_query = base_query.where(Job.experience_level == experience_level)
    if tech_stack:
        # OR semantics: a job matches if it has AT LEAST ONE of the
        # requested tags. Chosen over AND ("must have every tag")
        # because job-search tag filters are normally used to broaden
        # relevant results ("show me React OR Vue roles"), not narrow
        # to postings mentioning every single selected technology.
        # `.contains([tag])` on a JSONB column checks tag membership in
        # the array via Postgres' `@>` containment operator.
        base_query = base_query.where(
            or_(*[Job.tech_stack.contains([tag]) for tag in tech_stack])
        )

    # Count total matches BEFORE pagination is applied, so the frontend
    # can render "142 results" and compute total pages correctly.
    count_query = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    # `joinedload(Job.company)` eager-loads each job's company in the
    # same query (one JOIN) instead of triggering a separate query per
    # job when the endpoint later reads `job.company.name` -- avoids
    # the classic N+1 query problem for a list endpoint.
    paginated_query = (
        base_query.options(joinedload(Job.company))
        .order_by(Job.source_updated_at.desc().nullslast(), Job.scraped_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(paginated_query)
    jobs = result.scalars().unique().all()

    return list(jobs), total


async def get_job_by_id(db: AsyncSession, job_id: uuid.UUID) -> Job | None:
    """
    Fetch a single job by id, with its company eager-loaded (same
    N+1-avoidance reasoning as list_jobs above). Returns None if not
    found or inactive -- the endpoint turns that into a 404. Excluding
    inactive jobs here (not just in list_jobs) means an old, removed
    posting's detail link stops resolving once it's gone from the
    source, rather than staying linkable forever.
    """
    query = (
        select(Job)
        .where(Job.id == job_id, Job.is_active.is_(True))
        .options(joinedload(Job.company))
    )
    result = await db.execute(query)
    return result.unique().scalar_one_or_none()


def compute_total_pages(total: int, page_size: int) -> int:
    """Shared helper so the endpoint and any future caller compute this identically."""
    if total == 0:
        return 0
    return math.ceil(total / page_size)
