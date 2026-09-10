import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "@/lib/api";

afterEach(() => vi.restoreAllMocks());

describe("api client", () => {
  it("GET /projects hits the same-origin proxy and returns JSON", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify([{ id: "p1" }]), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    const out = await api.listProjects();
    expect(fetchMock).toHaveBeenCalledWith("/api/projects");
    expect(out[0].id).toBe("p1");
  });

  it("throws on non-ok responses", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("nope", { status: 500 })));
    await expect(api.listProjects()).rejects.toThrow("500");
  });

  it("POST /ask sends a JSON body", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify({ answer: "x" }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    await api.ask("p1", { question: "q" });
    const init = fetchMock.mock.calls[0][1];
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body).question).toBe("q");
  });

  it("GET /projects/:id/dossier hits the proxy and returns the dossier", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        new Response(JSON.stringify({ project_id: "nur_navoi_solar" }), { status: 200 }),
      );
    vi.stubGlobal("fetch", fetchMock);
    const out = await api.getDossier("nur_navoi_solar");
    expect(fetchMock).toHaveBeenCalledWith("/api/projects/nur_navoi_solar/dossier");
    expect(out.project_id).toBe("nur_navoi_solar");
  });
});
