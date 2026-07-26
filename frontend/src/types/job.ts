/**
 * Mirrors app/schemas/job.py on the backend exactly -- keep these two
 * in sync whenever the API response shape changes.
 */

export interface Job {
  id: string;
  title: string;
  company_name: string;
  location: string | null;
  department: string | null;
  experience_level: string | null;
  tech_stack: string[];
  description_preview: string | null;
  absolute_url: string;
  source_updated_at: string | null; // ISO 8601 timestamp, or null
  scraped_at: string; // ISO 8601 timestamp
}

/** Full job detail -- everything Job has, plus the untruncated description. */
export interface JobDetail extends Job {
  description_text: string | null;
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
  experience_level?: string;
  tech_stack?: string[];
  page?: number;
  page_size?: number;
}

/**
 * Fixed experience-level buckets -- mirrors
 * EXPERIENCE_LEVEL_PATTERNS in the backend's tech_taxonomy.py.
 * Kept as a small hardcoded list here rather than fetched from an
 * API (unlike tech stack tags): this list is small, stable, and
 * defined by the backend's extraction logic itself, not by
 * accumulated job data -- an API round-trip would add latency for
 * something that essentially never changes.
 */
export const EXPERIENCE_LEVELS = [
  "Intern",
  "Entry",
  "Mid",
  "Senior",
  "Staff",
  "Principal",
  "Lead",
] as const;
