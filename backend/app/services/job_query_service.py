"""
Job listing/search query logic, kept separate from the HTTP layer
(app/api/v1/endpoints/jobs.py) -- same pattern as auth_service.py:
the endpoint stays thin, the actual query-building logic lives here
where it's independently readable and testable.
"""

import math

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.company import Company
from app.models.job import Job


async def list_jobs(
    db: AsyncSession,
    title: str | None,
    location: str | None,
    company: str | None,
    page: int,
    page_size: int,
) -> tuple[list[Job], int]:
    """
    Return (jobs_for_this_page, total_matching_count) for the given
    filters. Filters are optional and combine with AND when more than
    one is provided.

    All three filters use case-insensitive partial matching (`ilike`)
    rather than exact match -- "engineer" should match "Senior Software
    Engineer", and "san fran" should match "San Francisco, CA". This is
    what makes a search box usable instead of requiring the exact
    stored string.
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


def compute_total_pages(total: int, page_size: int) -> int:
    """Shared helper so the endpoint and any future caller compute this identically."""
    if total == 0:
        return 0
    return math.ceil(total / page_size)
