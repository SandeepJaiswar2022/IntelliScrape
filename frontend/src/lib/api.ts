import type { JobDetail, JobFilters, PaginatedJobs } from "../types/job";

// Falls back to the local backend's default port with a loud console
// warning, rather than silently building a request URL containing the
// literal string "undefined" -- a missing .env file should be obvious
// immediately (broken job list + a clear message in devtools), not a
// silent mystery of "why is nothing loading".
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
if (!import.meta.env.VITE_API_BASE_URL) {
  console.warn(
    "VITE_API_BASE_URL is not set (missing frontend/.env?) -- falling back to http://localhost:8000"
  );
}

/**
 * Thrown for any non-2xx response, carrying the HTTP status so callers
 * can distinguish e.g. a 404 from a 500 -- used by the detail page to
 * show a proper "job not found" state instead of a generic error.
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * Fetch a page of jobs from the backend, applying whichever filters
 * are provided. Undefined/empty filters are omitted from the query
 * string entirely rather than sent as empty params. `tech_stack` is
 * repeated as multiple `tech_stack=` params (matches FastAPI's
 * `list[str] | None = Query(None)` parsing on the backend).
 */
export async function fetchJobs(filters: JobFilters): Promise<PaginatedJobs> {
  const params = new URLSearchParams();

  if (filters.title) params.set("title", filters.title);
  if (filters.location) params.set("location", filters.location);
  if (filters.experience_level) params.set("experience_level", filters.experience_level);
  if (filters.tech_stack) {
    for (const tag of filters.tech_stack) {
      params.append("tech_stack", tag);
    }
  }
  params.set("page", String(filters.page ?? 1));
  params.set("page_size", String(filters.page_size ?? 20));

  const response = await fetch(`${API_BASE_URL}/api/v1/jobs?${params.toString()}`);

  if (!response.ok) {
    throw new ApiError(`Failed to load jobs (${response.status})`, response.status);
  }

  return response.json() as Promise<PaginatedJobs>;
}

/** Fetch a single job's full detail by id. Throws ApiError(404) if not found. */
export async function fetchJobById(id: string): Promise<JobDetail> {
  const response = await fetch(`${API_BASE_URL}/api/v1/jobs/${id}`);

  if (!response.ok) {
    throw new ApiError(`Failed to load job (${response.status})`, response.status);
  }

  return response.json() as Promise<JobDetail>;
}

/**
 * Fetch every canonical tech-stack tag the backend can produce --
 * powers the autocomplete filter input's suggestion list.
 */
export async function fetchTechStackOptions(): Promise<string[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/jobs/tech-stack-options`);

  if (!response.ok) {
    throw new ApiError(`Failed to load tech stack options (${response.status})`, response.status);
  }

  return response.json() as Promise<string[]>;
}
