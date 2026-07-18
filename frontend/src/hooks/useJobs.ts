import { useQuery } from "@tanstack/react-query";
import { fetchJobs } from "../lib/api";
import type { JobFilters } from "../types/job";

/**
 * Wraps the jobs list fetch in TanStack Query, which gives us (for
 * free, without hand-rolling any of it): loading/error states, caching
 * by query key (switching filters and back reuses the cached result
 * instead of re-fetching), and automatic request de-duplication if
 * multiple components ask for the same filters at once.
 *
 * The query key includes every filter value -- this is what tells
 * React Query "these are different queries, don't share a cache
 * entry" whenever any filter or page changes.
 */
export function useJobs(filters: JobFilters) {
  return useQuery({
    queryKey: ["jobs", filters],
    queryFn: () => fetchJobs(filters),
    // Keep the previous page's data visible while a new page/filter
    // loads, instead of flashing a loading spinner on every filter
    // keystroke -- much smoother for a search-as-you-type experience.
    placeholderData: (previousData) => previousData,
  });
}
