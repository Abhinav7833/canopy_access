import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export const useProjects = () => useQuery({ queryKey: ["projects"], queryFn: api.listProjects });
export const useProject = (id: string) =>
  useQuery({ queryKey: ["project", id], queryFn: () => api.getProject(id) });
export const useBoundary = (id: string) =>
  useQuery({ queryKey: ["boundary", id], queryFn: () => api.getBoundary(id) });
export const useImagery = (id: string) =>
  useQuery({ queryKey: ["imagery", id], queryFn: () => api.getImagery(id) });
export const useEvidence = (id: string, enabled = true) =>
  useQuery({ queryKey: ["evidence", id], queryFn: () => api.getEvidence(id), enabled });
export const useDossier = (id: string) =>
  useQuery({ queryKey: ["dossier", id], queryFn: () => api.getDossier(id) });

/** The asset's most recently generated memo (or null). Backed by the query cache, so it
 * survives leaving the memo tab and coming back — unlike the generate mutation's own state,
 * which is discarded when the page unmounts. The key is shared with the generate mutation,
 * which writes the fresh memo straight into this cache. */
export const reportKey = (id: string) => ["report", id] as const;
export const useLatestReport = (id: string) =>
  useQuery({
    queryKey: reportKey(id),
    queryFn: () => api.getLatestReport(id),
    // The on-page "Generate" is the only writer and updates this cache directly, so returning
    // to the tab needn't re-fetch a memo already in hand.
    staleTime: Infinity,
  });
