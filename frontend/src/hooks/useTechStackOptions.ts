import { useQuery } from "@tanstack/react-query";
import { fetchTechStackOptions } from "../lib/api";

/**
 * Fetches the full canonical tag list once and caches it aggressively
 * -- this list only changes when the backend's taxonomy is updated
 * (a code deploy, not something that happens live), so there's no
 * reason to ever refetch it within a session.
 */
export function useTechStackOptions() {
  return useQuery({
    queryKey: ["tech-stack-options"],
    queryFn: fetchTechStackOptions,
    staleTime: Infinity,
  });
}
