# ============================================================
# IntelliScrape backend — FastAPI auth service image
# Single-stage build; kept simple for the first milestone.
# (A multi-stage build can be introduced later to shrink image
# size once the dependency list grows.)
# ============================================================

FROM python:3.12-slim

# Prevents Python from writing .pyc files and buffering stdout/stderr —
# both make container logs behave predictably.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install OS-level build deps needed by asyncpg/argon2-cffi wheels on slim images.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first so Docker can cache this layer
# and skip reinstalling when only app code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and migration config.
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .

EXPOSE 8000

# Default command for production-like runs (no --reload).
# docker-compose overrides this with --reload for local dev.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
