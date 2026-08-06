"""
Job table.

The unique constraint on (source, source_job_id) is the entire dedup
mechanism for this milestone: re-running the Greenhouse fetch (whether
manually, or every 6 hours via Celery beat) upserts against this
constraint instead of creating duplicate rows -- see
app/services/job_ingestion_service.py for the actual
INSERT ... ON CONFLICT DO UPDATE logic that relies on it.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        # This is what makes re-running ingestion idempotent: the same
        # job posting from the same source always maps to the same row.
        UniqueConstraint("source", "source_job_id", name="uq_job_source_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )

    # "greenhouse" today -- mirrors Company.source, kept on Job too so
    # the uniqueness constraint doesn't require a join to enforce.
    source: Mapped[str] = mapped_column(String(50), nullable=False)

    # The source's own job ID (Greenhouse's "id" field). Stored as a
    # string even though Greenhouse's is numeric -- other sources may
    # use non-numeric IDs, and this column should never need to change
    # type when a second source is added.
    source_job_id: Mapped[str] = mapped_column(String(255), nullable=False)

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[str | None] = mapped_column(Text, nullable=True)
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Full HTML job description as provided by the source. Rendered
    # as-is by the frontend later (with sanitization at render time) --
    # stored raw here since that's exactly what the source gives us.
    description_html: Mapped[str | None] = mapped_column(Text, nullable=True)

    absolute_url: Mapped[str] = mapped_column(String(1000), nullable=False)

    # --- Derived fields (computed at ingestion time, not from the source) ---
    # Neither of these exists in Greenhouse's data -- both are extracted
    # from title/description via rule-based keyword matching. See
    # app/services/job_extraction_service.py for the "why rule-based,
    # not LLM" reasoning and known precision/recall limitations.
    #
    # None when the title has no explicit level signal (e.g. plain
    # "Software Engineer") -- deliberately not defaulted to a guessed
    # bucket like "Mid", since that would assert something the posting
    # never actually said.
    experience_level: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # JSONB (not a separate join table) is the right call at this
    # scale: tech_stack is always read/written as a whole list per job,
    # never queried independently of its job, and Postgres' JSONB
    # containment operators (`@>`, used via SQLAlchemy's `.contains()`)
    # give us efficient "job has tag X" filtering without needing a
    # many-to-many table + joins for what's fundamentally a small,
    # denormalized tag list.
    tech_stack: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)

    # When the SOURCE says this posting was last updated -- distinct
    # from `scraped_at` below, which is when WE last saw it. The two
    # diverge whenever a posting hasn't changed between scrape runs.
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Whether this posting was present in the most recent successful
    # fetch for its company. Not yet acted on anywhere in this
    # milestone, but the column exists now so a later milestone can
    # mark postings inactive once they disappear from the source,
    # without a schema migration at that point.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    company: Mapped["Company"] = relationship(back_populates="jobs")
