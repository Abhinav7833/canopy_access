import type {
  AskResponse,
  Boundary,
  Dossier,
  Evidence,
  Imagery,
  ProjectDetail,
  ProjectSummary,
  Report,
} from "@/lib/types";

/** Error shape thrown for any non-2xx response. Carries the HTTP status and,
 * when the backend responds with the `{"error":{"code","message"}}` envelope
 * (see backend/app/core/errors.py), the machine-readable code + human message. */
export class ApiError extends Error {
  status: number;
  code?: string;
  constructor(message: string, status: number, code?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

/** True when a request failed because the backend LLM isn't configured. Keyed off the
 * backend's machine-readable error code (see backend/app/core/errors.py) rather than the
 * HTTP status alone — other failures can also surface as 503 and shouldn't be conflated. */
export function isLlmUnavailable(error: unknown): boolean {
  return error instanceof ApiError && error.code === "llm_not_configured";
}

async function errorFrom(path: string, method: string, res: Response): Promise<ApiError> {
  try {
    const body = await res.json();
    const message = body?.error?.message;
    const code = body?.error?.code;
    if (typeof message === "string") return new ApiError(message, res.status, code);
  } catch {
    // response wasn't JSON / didn't match the error envelope — fall through
  }
  return new ApiError(`${method} ${path} -> ${res.status}`, res.status);
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`/api${path}`);
  if (!res.ok) throw await errorFrom(path, "GET", res);
  return res.json() as Promise<T>;
}
async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`/api${path}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw await errorFrom(path, "POST", res);
  return res.json() as Promise<T>;
}

export const api = {
  listProjects: () => get<ProjectSummary[]>("/projects"),
  getProject: (id: string) => get<ProjectDetail>(`/projects/${id}`),
  getBoundary: (id: string) => get<Boundary>(`/projects/${id}/boundary`),
  getImagery: (id: string) => get<Imagery>(`/projects/${id}/imagery`),
  getEvidence: (id: string) => get<Evidence[]>(`/projects/${id}/evidence`),
  getDossier: (id: string) => get<Dossier>(`/projects/${id}/dossier`),
  ask: (id: string, body: { question: string; allowed_evidence_ids?: string[] }) =>
    post<AskResponse>(`/projects/${id}/ask`, body),
  createReport: (id: string, body: { report_type?: string }) =>
    post<Report>(`/projects/${id}/reports`, body),
  getReport: (reportId: string) => get<Report>(`/reports/${reportId}`),
  // Null when no memo has been generated for the asset yet.
  getLatestReport: (id: string) => get<Report | null>(`/projects/${id}/reports/latest`),
};
