"""
Request/response schemas for the jobs listing/search/detail API.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel


class JobResponse(BaseModel):
    """
    Public-facing job representation for the LIST endpoint. Flattens
    `company_name` onto the job itself (rather than nesting a whole
    Company object) since job cards only ever need the name, not the
    full company record. Includes `description_preview` (short, plain
    text) but deliberately NOT the full description -- see
    JobDetailResponse for that, fetched separately per-job so the list
    endpoint's payload doesn't balloon with full HTML/text for every
    row on every page.
    """

    id: uuid.UUID
    title: str
    company_name: str
    location: str | None
    department: str | None
    experience_level: str | None
    tech_stack: list[str]
    description_preview: str | None
    absolute_url: str
    source_updated_at: datetime | None
    scraped_at: datetime

    model_config = {"from_attributes": True}


class JobDetailResponse(JobResponse):
    """
    Full job representation for GET /jobs/{id} -- everything
    JobResponse has, plus the full plain-text description. This is the
    stable, linkable per-job resource the detail page renders, and the
    intended foundation for later features that need to reference a
    specific posting (e.g. resume matching against this exact job).
    """

    description_text: str | None


class PaginatedJobsResponse(BaseModel):
    """Standard paginated list envelope -- reused for any list endpoint later."""

    items: list[JobResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
