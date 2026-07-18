"""
Jobs listing/search endpoint.

Deliberately public (no auth dependency) -- browsing jobs shouldn't
require an account, same as every real job board. Auth gets layered
onto other features (saved jobs, alerts, resume matching) in a later
milestone, not onto basic browsing.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.job import JobResponse, PaginatedJobsResponse
from app.services.job_query_service import compute_total_pages, list_jobs

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=PaginatedJobsResponse)
async def get_jobs(
    title: str | None = Query(
        None, description="Filter by job title, case-insensitive partial match (e.g. 'engineer')"
    ),
    location: str | None = Query(
        None, description="Filter by location, case-insensitive partial match (e.g. 'remote', 'new york')"
    ),
    company: str | None = Query(
        None, description="Filter by company name, case-insensitive partial match"
    ),
    page: int = Query(1, ge=1, description="1-indexed page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page, max 100"),
    db: AsyncSession = Depends(get_db),
) -> PaginatedJobsResponse:
    """
    List job postings with optional filtering and pagination.

    NOTE on scope: the project roadmap's Phase 2 also mentions a
    tech-stack filter -- that's intentionally not implemented yet,
    because the current `jobs` table has no tech_stack column (nothing
    in the Greenhouse ingestion pipeline extracts one yet). Adding it
    is a schema + ingestion change, not just an endpoint change, so
    it's deferred rather than half-implemented here.
    """
    jobs, total = await list_jobs(
        db, title=title, location=location, company=company, page=page, page_size=page_size
    )

    items = [
        JobResponse(
            id=job.id,
            title=job.title,
            company_name=job.company.name,
            location=job.location,
            department=job.department,
            absolute_url=job.absolute_url,
            source_updated_at=job.source_updated_at,
            scraped_at=job.scraped_at,
        )
        for job in jobs
    ]

    return PaginatedJobsResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=compute_total_pages(total, page_size),
    )
