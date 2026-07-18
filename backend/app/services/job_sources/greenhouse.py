"""
Greenhouse Job Board API source.

This is deliberately the FIRST data source for this project (see the
roadmap's Section 0): it's an explicitly public, unauthenticated API
that Greenhouse documents and intends for exactly this kind of use --
not an adversarial scrape of a site that's actively trying to block
bots. No API key, no login, no ToS violation.

API reference: https://developers.greenhouse.io/job-board.html
Endpoint used: GET /v1/boards/{board_token}/jobs?content=true
  - board_token: the slug in a company's public careers URL, e.g.
    https://job-boards.greenhouse.io/stripe -> token is "stripe"
  - content=true: includes the full HTML job description in the
    response (without it, you only get title/location/id)
"""

import logging
from datetime import datetime

import httpx

from app.services.job_sources.base import JobSource, RawJobPosting

logger = logging.getLogger(__name__)

_GREENHOUSE_API_BASE = "https://boards-api.greenhouse.io/v1/boards"
_REQUEST_TIMEOUT_SECONDS = 15.0


class GreenhouseJobSource(JobSource):
    """Fetches job postings for a configured list of Greenhouse board tokens."""

    def __init__(self, company_tokens: list[str]):
        self._company_tokens = company_tokens

    async def fetch_jobs(self) -> list[RawJobPosting]:
        """
        Fetch jobs for every configured company, one HTTP request per
        company (Greenhouse's API has no "give me multiple companies at
        once" endpoint).

        One shared httpx.AsyncClient is reused across all requests in
        this call -- this lets httpx reuse the underlying TCP
        connection pool instead of opening a fresh connection per
        company, which matters more as the company list grows toward
        20+.
        """
        all_postings: list[RawJobPosting] = []
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT_SECONDS) as client:
            for token in self._company_tokens:
                try:
                    postings = await self._fetch_jobs_for_company(client, token)
                    logger.info("Fetched %d jobs for '%s'", len(postings), token)
                    all_postings.extend(postings)
                except httpx.HTTPError as exc:
                    # One company's API hiccup (timeout, 404 for a typo'd
                    # token, Greenhouse-side error) should never abort
                    # the whole run -- log it and keep going with the
                    # rest of the list. This matters a lot once the
                    # company list grows past a handful.
                    logger.warning("Failed to fetch jobs for '%s': %s", token, exc)
        return all_postings

    async def _fetch_jobs_for_company(
        self, client: httpx.AsyncClient, company_token: str
    ) -> list[RawJobPosting]:
        url = f"{_GREENHOUSE_API_BASE}/{company_token}/jobs"
        response = await client.get(url, params={"content": "true"})
        response.raise_for_status()  # turns a 404/500 into httpx.HTTPStatusError
        payload = response.json()

        return [
            self._parse_job(company_token, raw_job) for raw_job in payload.get("jobs", [])
        ]

    def _parse_job(self, company_token: str, raw_job: dict) -> RawJobPosting:
        """Convert one raw Greenhouse job dict into a source-agnostic RawJobPosting."""
        location = raw_job.get("location") or {}

        # Greenhouse nests department under a list (a job can technically
        # belong to more than one) -- we keep only the first for
        # simplicity; this is enough for filtering/display in this milestone.
        departments = raw_job.get("departments") or []
        department_name = departments[0]["name"] if departments else None

        source_updated_at = self._parse_greenhouse_timestamp(raw_job.get("updated_at"))

        # absolute_url should always be present in practice, but we
        # build a sane fallback rather than let a missing field crash
        # ingestion for an otherwise-valid job posting.
        absolute_url = raw_job.get("absolute_url") or (
            f"https://job-boards.greenhouse.io/{company_token}/jobs/{raw_job.get('id')}"
        )

        return RawJobPosting(
            source="greenhouse",
            source_job_id=str(raw_job["id"]),
            source_company_token=company_token,
            # Greenhouse's /jobs list endpoint doesn't return a
            # human-friendly company display name -- using the token
            # itself for now. Refining this (e.g. via the separate
            # /boards/{token} endpoint, which does return a name) is a
            # small later improvement, not a blocker for this milestone.
            company_name=company_token,
            title=raw_job.get("title") or "Untitled role",
            location=location.get("name"),
            department=department_name,
            description_html=raw_job.get("content"),
            absolute_url=absolute_url,
            source_updated_at=source_updated_at,
        )

    @staticmethod
    def _parse_greenhouse_timestamp(raw_value: str | None) -> datetime | None:
        """
        Greenhouse returns ISO-8601 timestamps like "2013-07-02T19:39:23Z".
        Python's datetime.fromisoformat doesn't accept a bare "Z" suffix
        (pre-3.11 quirk that's safest to just always handle explicitly),
        so it's normalized to "+00:00" first.
        """
        if not raw_value:
            return None
        try:
            return datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
        except ValueError:
            # A malformed timestamp from the source shouldn't crash
            # ingestion for an otherwise-valid job posting.
            logger.warning("Could not parse Greenhouse timestamp: %r", raw_value)
            return None
