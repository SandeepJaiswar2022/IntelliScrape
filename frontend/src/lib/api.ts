import type { JobDetail, JobFilters, PaginatedJobs } from "../types/job";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
if (!import.meta.env.VITE_API_BASE_URL) {
  console.warn(
    "VITE_API_BASE_URL is not set (missing frontend/.env?) -- falling back to http://localhost:8000"
  );
}

/**
 * Thrown for any non-2xx response, carrying the HTTP status so callers
 * can distinguish e.g. a 404 from a 500 -- and, importantly, a 401
 * (expired/invalid access token), which AuthContext's QueryClient
 * error handler watches for globally to clear the session and bounce
 * back to /login rather than showing a confusing generic error.
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
 * Builds the Authorization header for an authenticated request.
 * `accessToken` is undefined only in the brief window before the
 * initial silent-refresh attempt resolves -- callers guard against
 * firing requests during that window via each hook's `enabled` option
 * (see hooks/useJobs.ts etc.), so this should never actually be
 * called with an empty token in practice, but returns an empty object
 * rather than a header with the literal string "undefined" either way.
 */
function authHeaders(accessToken: string | undefined): HeadersInit {
  return accessToken ? { Authorization: `Bearer ${accessToken}` } : {};
}

/**
 * Fetch a page of jobs from the backend, applying whichever filters
 * are provided. Undefined/empty filters are omitted from the query
 * string entirely rather than sent as empty params. `tech_stack` is
 * repeated as multiple `tech_stack=` params (matches FastAPI's
 * `list[str] | None = Query(None)` parsing on the backend).
 */
export async function fetchJobs(
  filters: JobFilters,
  accessToken: string | undefined
): Promise<PaginatedJobs> {
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

  const response = await fetch(`${API_BASE_URL}/api/v1/jobs?${params.toString()}`, {
    headers: authHeaders(accessToken),
  });

  if (!response.ok) {
    throw new ApiError(`Failed to load jobs (${response.status})`, response.status);
  }

  return response.json() as Promise<PaginatedJobs>;
}

/** Fetch a single job's full detail by id. Throws ApiError(404) if not found. */
export async function fetchJobById(id: string, accessToken: string | undefined): Promise<JobDetail> {
  const response = await fetch(`${API_BASE_URL}/api/v1/jobs/${id}`, {
    headers: authHeaders(accessToken),
  });

  if (!response.ok) {
    throw new ApiError(`Failed to load job (${response.status})`, response.status);
  }

  return response.json() as Promise<JobDetail>;
}

/**
 * Fetch every canonical tech-stack tag the backend can produce --
 * powers the autocomplete filter input's suggestion list.
 */
export async function fetchTechStackOptions(accessToken: string | undefined): Promise<string[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/jobs/tech-stack-options`, {
    headers: authHeaders(accessToken),
  });

  if (!response.ok) {
    throw new ApiError(`Failed to load tech stack options (${response.status})`, response.status);
  }

  return response.json() as Promise<string[]>;
}

/**
 * Trigger the admin-only manual scrape. Returns the same summary shape
 * the Celery task itself returns ({ companies_processed, jobs_processed }).
 */
export async function triggerAdminScrape(
  accessToken: string | undefined
): Promise<{ companies_processed: number; jobs_processed: number }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/admin/scrape`, {
    method: "POST",
    headers: authHeaders(accessToken),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body && typeof body === "object" && "detail" in body ? String(body.detail) : null;
    throw new ApiError(detail ?? `Scrape failed (${response.status})`, response.status);
  }

  return response.json();
}