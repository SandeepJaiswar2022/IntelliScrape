"""
Database engine/session setup using SQLAlchemy 2.0's async API.

Design notes:
  - One shared async engine for the whole app (connection pooling handled
    by SQLAlchemy/asyncpg internally).
  - `get_db` is a FastAPI dependency: each request gets its own session,
    and the session is always closed afterwards, even if the request
    raises an exception (the `async with` block guarantees cleanup).
  - `Base` is the declarative base every ORM model inherits from — Alembic
    also imports this to know what tables should exist.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# `echo=settings.DEBUG` prints every SQL statement to the logs in dev —
# genuinely useful while building, noisy in production, hence tied to DEBUG.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,  # detects and discards dead connections automatically
)

# `expire_on_commit=False` means objects stay usable after commit without
# triggering a fresh DB round-trip just to re-read attributes — convenient
# for returning ORM objects straight out of a service function.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields a request-scoped DB session.

    Usage in an endpoint:
        async def my_endpoint(db: AsyncSession = Depends(get_db)):
            ...

    The `async with` ensures the session (and its underlying connection)
    is released back to the pool as soon as the request finishes,
    regardless of success or failure.
    """
    async with AsyncSessionLocal() as session:
        yield session


@asynccontextmanager
async def task_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    A separate DB session helper specifically for use inside Celery
    tasks -- deliberately NOT reusing the `engine`/`AsyncSessionLocal`
    defined above. Here's why this distinction matters:

    Celery's default worker pool ("prefork") starts by forking child
    processes from one parent process. If an async engine/connection
    pool were created at module-import time (as `engine` above is, for
    the FastAPI process), and Celery's parent process imported this
    same module before forking, every forked child would inherit a
    reference to the *same* underlying socket/event-loop state --
    async database drivers like asyncpg do not support this safely,
    and it leads to hard-to-debug connection errors or hangs.

    The fix: build a brand-new engine *inside* this function, which
    only ever runs after a worker process already exists (i.e. after
    any forking is done) and dispose of it when the task finishes. The
    overhead of a fresh connection per task run is a total non-issue
    for a task that runs every few hours -- correctness matters far
    more than shaving milliseconds here.
    """
    task_engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    task_session_factory = async_sessionmaker(
        bind=task_engine, class_=AsyncSession, expire_on_commit=False
    )
    try:
        async with task_session_factory() as session:
            yield session
    finally:
        await task_engine.dispose()
