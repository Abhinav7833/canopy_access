import { act, fireEvent, render, screen } from "@testing-library/react";
import { Suspense } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Boundary, Dossier, ImageLayer, Imagery, ObservationSeriesPoint } from "@/lib/types";
import type { MapImage } from "@/components/map/EvidenceMap";

// Captures what the map was actually asked to draw, so a test can tell a real multi-frame
// timelapse from a single reference frame.
const drawn: { images: MapImage[] } = { images: [] };
vi.mock("@/components/map/EvidenceMap", () => ({
  EvidenceMap: ({ images }: { images: MapImage[] }) => {
    drawn.images = images;
    return <div data-testid="map" />;
  },
}));

const boundary: Boundary = {
  type: "Feature",
  geometry: { type: "Polygon", coordinates: [[[0, 0], [0, 1], [1, 1], [0, 0]]] },
  properties: { project_id: "p1", area_hectares: 240 },
};

const reference: ImageLayer = {
  key: "aoi_reference_rgb.png",
  label: "aoi reference rgb",
  url: "/static/p1/aoi_reference_rgb.png",
  kind: "rgb",
  source: "Esri World Imagery",
  date: null,
};

// A dated RGB capture, keyed and dated like a real Wayback timelapse frame.
const frame = (date: string): ImageLayer => ({
  key: `wayback_${date}_rgb.jpg`,
  label: `wayback ${date} rgb`,
  url: `/static/p1/wayback_${date}_rgb.jpg`,
  kind: "rgb",
  source: "Esri World Imagery",
  date,
});

const snapshot = (date: string): ObservationSeriesPoint => ({
  date,
  image_key: null,
  footprint_ha: 180,
  ndvi: 0.2,
  note: `snapshot ${date}`,
});

function mockQueries(series: ObservationSeriesPoint[], layers: ImageLayer[]) {
  const imagery: Imagery = { project_id: "p1", layers };
  const dossier = { observation_series: series } as unknown as Dossier;
  vi.doMock("@/lib/queries", () => ({
    useBoundary: () => ({ data: boundary, isError: false }),
    useImagery: () => ({ data: imagery, isError: false }),
    useDossier: () => ({ data: dossier, isLoading: false, isError: false }),
    useProject: () => ({ data: { asset_type: "solar" } }),
  }));
}

async function renderObserve() {
  const { default: Observe } = await import("./page");
  // The page reads its route params with `use()`, so the first render suspends; the act
  // scope has to be awaited for React to retry once the params promise resolves.
  await act(async () => {
    render(
      <Suspense fallback={null}>
        <Observe params={Promise.resolve({ id: "p1" })} />
      </Suspense>,
    );
  });
}

describe("Observe (timeline)", () => {
  beforeEach(() => {
    vi.resetModules();
    drawn.images = [];
  });

  it("shows the reference frame and no slider when there are no dated frames", async () => {
    mockQueries([snapshot("2019-04-01"), snapshot("2021-09-15")], [reference]);
    await renderObserve();

    expect(drawn.images).toEqual([{ id: "reference", url: reference.url, opacity: 1 }]);
    expect(screen.queryByRole("slider")).not.toBeInTheDocument();
    expect(screen.getByText("Esri World Imagery")).toBeInTheDocument();
  });

  it("shows a single dated frame without a slider", async () => {
    mockQueries([snapshot("2021-09-15")], [reference, frame("2021-09-15")]);
    await renderObserve();

    expect(drawn.images.map((i) => i.url)).toEqual(["/static/p1/wayback_2021-09-15_rgb.jpg"]);
    expect(screen.queryByRole("slider")).not.toBeInTheDocument();
  });

  it("plays a dated timelapse once two or more frames exist, oldest first", async () => {
    // Layers deliberately out of order — the page sorts by date.
    mockQueries([snapshot("2019-04-01")], [reference, frame("2024-06-27"), frame("2019-06-26")]);
    await renderObserve();

    expect(screen.getByRole("slider")).toBeInTheDocument();
    const urls = drawn.images.map((i) => i.url);
    expect(urls).toContain("/static/p1/wayback_2019-06-26_rgb.jpg");
    expect(urls).toContain("/static/p1/wayback_2024-06-27_rgb.jpg");
    // Exactly one frame is visible; the oldest is first and shown initially.
    expect(drawn.images.filter((i) => i.opacity === 1)).toHaveLength(1);
    expect(drawn.images[0].url).toBe("/static/p1/wayback_2019-06-26_rgb.jpg");
    expect(drawn.images[0].opacity).toBe(1);
  });

  it("scrubbing the slider selects that frame", async () => {
    mockQueries([snapshot("2019-04-01")], [reference, frame("2019-06-26"), frame("2024-06-27")]);
    await renderObserve();

    await act(async () => {
      fireEvent.change(screen.getByRole("slider"), { target: { value: "1" } });
    });
    const visible = drawn.images.find((i) => i.opacity === 1);
    expect(visible?.url).toBe("/static/p1/wayback_2024-06-27_rgb.jpg");
  });
});
