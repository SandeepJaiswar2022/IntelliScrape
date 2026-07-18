"""
Celery application setup.

=== What Celery actually is, if you've never used it ===

FastAPI handles HTTP requests: someone hits an endpoint, your code runs,
a response goes back -- all within one request's lifetime, usually
milliseconds. That model breaks down for work that is either (a) slow
(calling 5 external APIs takes seconds, not milliseconds) or (b) not
triggered by a request at all (e.g. "fetch new jobs every 6 hours,
whether or not anyone is using the site right now").

Celery solves this by moving that work OUT of the request/response
cycle entirely, into separate, independent worker processes:

  1. Something (your code, or a schedule) says "please run this task"
     and drops a message describing the task onto a queue.
  2. That queue lives in Redis (in this project) -- Redis's job here is
     purely to be the mailbox between "I want this done" and "a worker
     will do it."
  3. One or more separate `celery worker` processes are constantly
     watching that queue. When a message appears, a worker picks it up
     and actually runs the corresponding Python function.
  4. The process that enqueued the task doesn't wait around for the
     result (unless it explicitly asks to) -- it's fire-and-forget.

Two moving pieces run alongside your FastAPI app because of this:
  - `celery worker`  -- the process that actually executes tasks.
  - `celery beat`    -- a scheduler that enqueues tasks on a timer (our
                         "every 6 hours, run the Greenhouse fetch" rule
                         lives here). Beat doesn't run tasks itself --
                         it just puts them on the queue on schedule,
                         same as if you'd triggered them manually.

Both are separate OS processes from your FastAPI app (see
docker-compose.yml: `celery_worker` and `celery_beat` are their own
containers) -- none of this runs inside the same process that serves
HTTP requests. That separation is the whole point: a slow or failing
scrape can never make your API slow or unresponsive for users.

=== Why this matters for THIS project specifically ===

Scraping Greenhouse for 5 (soon 20+) companies means making several
HTTP calls to an external service that might be slow or occasionally
fail. That's exactly the kind of work that has no business happening
inside a web request. Celery lets it run on its own schedule, retry on
failure, and never touch the user-facing API's performance.
"""

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "intelliscrape",
    # `broker` is where tasks get enqueued (the "mailbox" described
    # above). `backend` is where task results get stored if/when
    # something asks for them -- we reuse the same Redis instance for
    # both since our volume is low; a bigger project might split them.
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    # Lets `celery events`/monitoring tools show task progress, not
    # just final success/failure -- cheap to enable, useful for debugging.
    task_track_started=True,
    # Hard/soft time limits protect a worker from hanging forever if an
    # external API (Greenhouse, or a future source) stalls mid-request.
    # Soft limit raises an exception the task can catch/clean up on;
    # hard limit forcibly kills the task if it ignores the soft one.
    task_soft_time_limit=120,
    task_time_limit=180,
)

# Tells Celery to look for `@celery_app.task` definitions inside
# app/tasks/ automatically, instead of importing each task module by
# hand here. As more task modules get added later (e.g. a Playwright
# scraping task), they're picked up for free as long as they live under
# app/tasks/.

from app.tasks import job_scraping_tasks  # noqa: E402,F401

# --- Beat schedule: recurring tasks ---
# This is the ONLY place "run every 6 hours" is defined. The task
# itself (app/tasks/job_scraping_tasks.py) has no idea it's being run
# on a schedule -- it's the same function whether triggered by beat,
# by a manual CLI call, or (later) by an API endpoint.
celery_app.conf.beat_schedule = {
    "fetch-greenhouse-jobs-every-6-hours": {
        "task": "app.tasks.job_scraping_tasks.fetch_greenhouse_jobs",
        "schedule": crontab(minute=0, hour="*/6"),
    },
}
