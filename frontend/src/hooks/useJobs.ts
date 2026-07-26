import { useQuery } from "@tanstack/react-query";
import { fetchJobs } from "../lib/api";
import type { JobFilters } from "../types/job";

/**
 * Wraps the jobs list fetch in TanStack Query. The query key includes
 * every filter value (now including experience_level and tech_stack)
 * -- this is what tells React Query "these are different queries,
 * don't share a cache entry" whenever any filter or page changes.
 */
export function useJobs(filters: JobFilters) {
  return useQuery({
    queryKey: ["jobs", filters],
    queryFn: () => fetchJobs(filters),
    placeholderData: (previousData) => previousData,
  });
}
