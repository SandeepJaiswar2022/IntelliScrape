import type { JobFilters, PaginatedJobs } from "../types/job";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

/**
 * Thrown for any non-2xx response, carrying the HTTP status so callers
 * (or React Query's error UI) can distinguish e.g. a 500 from a 404 if
 * that ever matters. Kept intentionally simple for this milestone --
 * a single error type is enough until there's a real reason to branch
 * on specific status codes in the UI.
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
 * string entirely rather than sent as empty params -- keeps request
 * URLs clean and matches exactly what the backend's Query(None, ...)
 * defaults expect.
 */
export async function fetchJobs(filters: JobFilters): Promise<PaginatedJobs> {
  const params = new URLSearchParams();

  if (filters.title) params.set("title", filters.title);
  if (filters.location) params.set("location", filters.location);
  params.set("page", String(filters.page ?? 1));
  params.set("page_size", String(filters.page_size ?? 20));

  const response = await fetch(`${API_BASE_URL}/api/v1/jobs?${params.toString()}`);

  if (!response.ok) {
    throw new ApiError(`Failed to load jobs (${response.status})`, response.status);
  }

  return response.json() as Promise<PaginatedJobs>;
}
