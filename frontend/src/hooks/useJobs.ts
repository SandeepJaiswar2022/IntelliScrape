import { useQuery } from "@tanstack/react-query";
import { fetchJobs } from "../lib/api";
import type { JobFilters } from "../types/job";
import { useAuth } from "../context/AuthContext";

/**
 * Wraps the jobs list fetch in TanStack Query. `enabled: Boolean(accessToken)`
 * holds the query back until the initial silent-refresh (see
 * AuthContext) has resolved one way or the other -- otherwise this
 * would fire an unauthenticated request and immediately 401 during
 * the brief window before we know if the user has a valid session.
 */
export function useJobs(filters: JobFilters) {
  const { accessToken } = useAuth();

  return useQuery({
    queryKey: ["jobs", filters],
    queryFn: () => fetchJobs(filters, accessToken ?? undefined),
    enabled: Boolean(accessToken),
    placeholderData: (previousData) => previousData,
  });
}