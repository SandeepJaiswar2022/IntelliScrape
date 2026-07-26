import { useQuery } from "@tanstack/react-query";
import { fetchJobById } from "../lib/api";

/**
 * Fetches one job's full detail by id. `enabled: Boolean(id)` guards
 * against firing a request with an undefined id during the brief
 * render before route params are available -- not strictly necessary
 * given how this is called, but a cheap, standard safeguard.
 */
export function useJob(id: string | undefined) {
  return useQuery({
    queryKey: ["job", id],
    queryFn: () => fetchJobById(id as string),
    enabled: Boolean(id),
  });
}
