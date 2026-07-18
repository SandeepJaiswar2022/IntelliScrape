"""
Source-agnostic job posting shape + the interface every job data
source must implement.

Why this abstraction exists (see the project roadmap's Section 0 on
scraping legality): LinkedIn/Naukri scraping is legally risky and
technically fragile, so this project deliberately starts with safe,
official sources like Greenhouse's public API. But the whole point of
building it this way is that adding a second, different source later
(Lever's API, a specific company's own career page, etc.) should NEVER
require touching the ingestion/task code -- only a new class here that
implements `fetch_jobs()` and returns the same `RawJobPosting` shape.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RawJobPosting:
    """
    A single job posting, normalized to a shape that doesn't know or
    care which source it came from. Ingestion code (see
    app/services/job_ingestion_service.py) depends ONLY on this shape --
    never on a specific source's raw JSON structure.
    """

    source: str  # e.g. "greenhouse"
    source_job_id: str  # the source's own ID for this specific job posting
    source_company_token: str  # the source's own ID for the company (e.g. Greenhouse board token)
    company_name: str
    title: str
    location: str | None
    department: str | None
    description_html: str | None
    absolute_url: str
    source_updated_at: datetime | None


class JobSource(ABC):
    """Common interface every job data source implementation follows."""

    @abstractmethod
    async def fetch_jobs(self) -> list[RawJobPosting]:
        """Fetch and return every current job posting from this source."""
        raise NotImplementedError
