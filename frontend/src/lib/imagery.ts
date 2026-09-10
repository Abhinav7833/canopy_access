import type { ImageLayer, Imagery } from "@/lib/types";

/** Resolve a snapshot's image_key to the URL of the layer serving it. Exact key match is the
 * contract; the case-insensitive basename fallback keeps real dated assets resolving if they
 * arrive with a path prefix or casing drift, rather than silently rendering an empty map. */
export function layerUrl(imagery: Imagery | undefined, key: string | null | undefined) {
  if (!key || !imagery) return undefined;
  const exact = imagery.layers.find((l) => l.key === key);
  if (exact) return exact.url;
  const base = key.split("/").pop()?.toLowerCase();
  return imagery.layers.find((l) => l.key.split("/").pop()?.toLowerCase() === base)?.url;
}

/** The RGB frame that best represents the AOI right now: the most recent capture, with undated
 * reference frames sorting last. Every screen showing "the satellite view" picks it this way, so
 * they can't drift apart on which frame that is. */
export function referenceFrame(imagery: Imagery | undefined) {
  return (imagery?.layers ?? [])
    .filter((l) => l.kind === "rgb")
    .reduce<ImageLayer | undefined>(
      (best, l) => (!best || (l.date ?? "") > (best.date ?? "") ? l : best),
      undefined,
    );
}
