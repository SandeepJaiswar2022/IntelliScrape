"""
Company table.

Deliberately source-agnostic: `source` + `source_company_token`
together identify a company within whichever source it came from
(Greenhouse today; Lever or a custom scraper later -- see
app/services/job_sources/base.py for the pluggable-source design this
supports). A future second source for the SAME real-world company
(e.g. if a company is findable both via Greenhouse and a direct career
page scrape) would currently create a second row -- that's a known,
deliberate simplification for this milestone; de-duplicating companies
across sources is a later-phase problem, not a Day 1 one.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Company(Base):
    __tablename__ = "companies"
    __table_args__ = (
        # The same company (by token) should never be inserted twice
        # for the same source -- this constraint is what makes the
        # "get or create" lookup in job_ingestion_service safe under
        # concurrent task runs.
        UniqueConstraint("source", "source_company_token", name="uq_company_source_token"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # "greenhouse" today; "lever", "career_page_scrape", etc. later.
    source: Mapped[str] = mapped_column(String(50), nullable=False)

    # The source's own identifier for this company, e.g. Greenhouse's
    # board token "stripe". Combined with `source` above, this is what
    # `job_ingestion_service` uses to find-or-create a Company row.
    source_company_token: Mapped[str] = mapped_column(String(255), nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    jobs: Mapped[list["Job"]] = relationship(back_populates="company")
