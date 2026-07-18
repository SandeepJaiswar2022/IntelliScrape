"""
Request/response schemas for the jobs listing API.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel


class JobResponse(BaseModel):
    """
    Public-facing job representation. Flattens `company_name` onto the
    job itself (rather than nesting a whole Company object) since the
    frontend's job cards only ever need the name, not the full company
    record -- keeps the response shape simple for this milestone.
    """

    id: uuid.UUID
    title: str
    company_name: str
    location: str | None
    department: str | None
    absolute_url: str
    source_updated_at: datetime | None
    scraped_at: datetime

    model_config = {"from_attributes": True}


class PaginatedJobsResponse(BaseModel):
    """Standard paginated list envelope -- reused for any list endpoint later."""

    items: list[JobResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
