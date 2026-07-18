/**
 * Mirrors app/schemas/job.py on the backend exactly -- keep these two
 * in sync whenever the API response shape changes. Deliberately kept
 * as plain interfaces (no validation library like zod) for this
 * milestone: the payload is small and fully controlled by our own
 * backend, so runtime validation would be defensive overkill right
 * now. Worth revisiting if this API ever accepts third-party data
 * directly into these shapes.
 */

export interface Job {
  id: string;
  title: string;
  company_name: string;
  location: string | null;
  department: string | null;
  absolute_url: string;
  source_updated_at: string | null; // ISO 8601 timestamp, or null
  scraped_at: string; // ISO 8601 timestamp
}

export interface PaginatedJobs {
  items: Job[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/** Query params accepted by GET /api/v1/jobs -- all optional. */
export interface JobFilters {
  title?: string;
  location?: string;
  page?: number;
  page_size?: number;
}
