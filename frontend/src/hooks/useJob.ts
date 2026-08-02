import { useQuery } from "@tanstack/react-query";
import { fetchJobById } from "../lib/api";
import { useAuth } from "../context/AuthContext";

/** Fetches one job's full detail by id -- see useJobs.ts for the `enabled` reasoning. */
export function useJob(id: string | undefined) {
  const { accessToken } = useAuth();

  return useQuery({
    queryKey: ["job", id],
    queryFn: () => fetchJobById(id as string, accessToken ?? undefined),
    enabled: Boolean(id) && Boolean(accessToken),
  });
}