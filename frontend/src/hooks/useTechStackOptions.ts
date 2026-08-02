import { useQuery } from "@tanstack/react-query";
import { fetchTechStackOptions } from "../lib/api";
import { useAuth } from "../context/AuthContext";

/**
 * Fetches the full canonical tag list once and caches it aggressively
 * -- this list only changes when the backend's taxonomy is updated
 * (a code deploy, not something that happens live).
 */
export function useTechStackOptions() {
  const { accessToken } = useAuth();

  return useQuery({
    queryKey: ["tech-stack-options"],
    queryFn: () => fetchTechStackOptions(accessToken ?? undefined),
    enabled: Boolean(accessToken),
    staleTime: Infinity,
  });
}