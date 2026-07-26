"""
Jobs listing/search/detail endpoints.

Deliberately public (no auth dependency) -- browsing jobs shouldn't
require an account, same as every real job board. Auth gets layered
onto other features (saved jobs, alerts, resume matching) in a later
milestone, not onto basic browsing.

=== Route ordering note ===
FastAPI matches routes in the order they're registered. The static
route `/jobs/tech-stack-options` is registered BEFORE the dynamic
`/jobs/{job_id}` route below -- if the order were reversed,
`/jobs/tech-stack-options` would incorrectly get captured by the
dynamic route (with "tech-stack-options" parsed as an attempted job
id, which would then 422 on UUID validation). This is a common FastAPI
footgun worth knowing about, not a one-off fix.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.tech_taxonomy import TECH_TAXONOMY
from app.schemas.job import JobDetailResponse, JobResponse, PaginatedJobsResponse
from app.services.job_query_service import compute_total_pages, get_job_by_id, list_jobs
from app.utils.html_text import strip_html, truncate_text

router = APIRouter(prefix="/jobs", tags=["jobs"])

# Plain-text preview length shown on job cards in the list view.
# Full, untruncated text is only sent by the detail endpoint below.
_DESCRIPTION_PREVIEW_LENGTH = 220


@router.get("/tech-stack-options", response_model=list[str])
async def get_tech_stack_options() -> list[str]:
    """
    Return every canonical tech-stack tag the extraction pipeline can
    produce -- powers the frontend's autocomplete filter input. Backed
    by the taxonomy module (single source of truth) rather than a
    distinct `SELECT DISTINCT tech_stack` query against the jobs table,
    so the full list is available even before any job has been tagged
    with every possible term.
    """
    return sorted(TECH_TAXONOMY.keys())


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
    experience_level: str | None = Query(
        None, description="Filter by experience level bucket (e.g. 'Senior', 'Entry')"
    ),
    tech_stack: list[str] | None = Query(
        None, description="Filter by tech stack tags -- matches jobs with ANY of the given tags"
    ),
    page: int = Query(1, ge=1, description="1-indexed page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page, max 100"),
    db: AsyncSession = Depends(get_db),
) -> PaginatedJobsResponse:
    """List job postings with optional filtering and pagination."""
    jobs, total = await list_jobs(
        db,
        title=title,
        location=location,
        company=company,
        experience_level=experience_level,
        tech_stack=tech_stack,
        page=page,
        page_size=page_size,
    )

    items = [
        JobResponse(
            id=job.id,
            title=job.title,
            company_name=job.company.name,
            location=job.location,
            department=job.department,
            experience_level=job.experience_level,
            tech_stack=job.tech_stack,
            description_preview=truncate_text(
                strip_html(job.description_html), _DESCRIPTION_PREVIEW_LENGTH
            )
            or None,
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


@router.get("/{job_id}", response_model=JobDetailResponse)
async def get_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> JobDetailResponse:
    """
    Fetch a single job's full detail, including the untruncated plain-
    text description. This is the stable resource a "View full
    details" link points to, and the intended foundation for later
    features that need to reference one specific posting (e.g. resume
    matching against this exact job) -- see the frontend detail page.
    """
    job = await get_job_by_id(db, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    plain = strip_html(job.description_html)

    print("RAW =", job.description_html[:80])
    print("PLAIN =", plain[:80])
    return JobDetailResponse(
        id=job.id,
        title=job.title,
        company_name=job.company.name,
        location=job.location,
        department=job.department,
        experience_level=job.experience_level,
        tech_stack=job.tech_stack,
        description_preview=truncate_text(
            strip_html(job.description_html), _DESCRIPTION_PREVIEW_LENGTH
        )
        or None,
        description_text=strip_html(job.description_html) or None,
        absolute_url=job.absolute_url,
        source_updated_at=job.source_updated_at,
        scraped_at=job.scraped_at,
    )
