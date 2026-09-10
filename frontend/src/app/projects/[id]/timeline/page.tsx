"use client";
import { use, useEffect, useState } from "react";
import { EvidenceMap, type MapImage } from "@/components/map/EvidenceMap";
import { Card, CardHeader, CardSkeleton } from "@/components/ui/Card";
import { DossierUnavailable } from "@/components/features/DossierUnavailable";
import { assetTypeConfig } from "@/lib/assetType";
import { formatDate, formatNumber } from "@/lib/format";
import { referenceFrame } from "@/lib/imagery";
import { useBoundary, useDossier, useImagery, useProject } from "@/lib/queries";

const FRAME_MS = 1000; // dwell per frame while playing

/** Step 3 of the narrative: the AOI's dated satellite captures played as a timelapse. Press
 * play or drag the slider to watch the asset change over time — every frame is a real, dated
 * capture, and the measured observation series is laid out below. */
export default function Observe({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: boundary, isError: boundaryError, error: boundaryErr } = useBoundary(id);
  const { data: imagery, isError: imageryError, error: imageryErr } = useImagery(id);
  const { data: dossier, isLoading, isError: dossierError, error: dossierErr } = useDossier(id);
  const { data: project } = useProject(id);
  const typeConfig = assetTypeConfig(project?.asset_type);

  // The timelapse frames: dated RGB captures oldest -> newest. Undated reference frames
  // (date null) are excluded — they have no place on a time axis.
  const frames = (imagery?.layers ?? [])
    .filter((l) => l.kind === "rgb" && l.date)
    .sort((a, b) => (a.date ?? "").localeCompare(b.date ?? ""));
  const hasTimelapse = frames.length >= 2;

  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(true);
  // Restart the timelapse when the project changes — a render-phase adjustment (applies before
  // paint) rather than an effect, per https://react.dev/learn/you-might-not-need-an-effect.
  const [prevId, setPrevId] = useState(id);
  if (id !== prevId) {
    setPrevId(id);
    setIndex(0);
    setPlaying(true);
  }
  const safeIndex = frames.length ? Math.min(index, frames.length - 1) : 0;

  // Auto-advance while playing. The functional update keeps the interval free of a stale index,
  // so it is created once per play/frame-count change rather than on every step.
  useEffect(() => {
    if (!playing || !hasTimelapse) return;
    const t = setInterval(() => setIndex((i) => (i + 1) % frames.length), FRAME_MS);
    return () => clearInterval(t);
  }, [playing, hasTimelapse, frames.length]);

  const reference = referenceFrame(imagery);
  // Preload every frame as its own map layer and drive the timelapse by opacity — switching a
  // paint property never reloads the source, so stepping is instant and flicker-free.
  const images: MapImage[] = frames.length
    ? frames.map((f, i) => ({ id: `frame-${i}`, url: f.url, opacity: i === safeIndex ? 1 : 0 }))
    : reference
      ? [{ id: "reference", url: reference.url, opacity: 1 }]
      : [];

  if (boundaryError || imageryError || dossierError)
    return (
      <DossierUnavailable error={dossierErr ?? imageryErr ?? boundaryErr} noun="observation series" />
    );
  if (isLoading || !boundary || !imagery || !dossier) return <CardSkeleton />;

  const series = dossier.observation_series ?? [];
  const current = frames[safeIndex];
  // When there is nothing to animate, caption the single frame the map is actually showing.
  const captionLayer = hasTimelapse ? undefined : frames[0] ?? reference;

  return (
    <div className="space-y-6">
      <p className="text-sm text-muted">
        A dated satellite timelapse of the AOI. Press play or drag the slider to watch the asset
        change over time; each frame is a real, dated capture traceable to its source.
      </p>
      <Card>
        <CardHeader
          title={typeConfig.observeTitle}
          action={
            <span className="text-xs text-muted">
              {formatDate(frames[0]?.date ?? series[0]?.date)} →{" "}
              {formatDate(frames[frames.length - 1]?.date ?? series[series.length - 1]?.date)}
              {hasTimelapse ? " · press play or scrub" : ""}
            </span>
          }
        />
        <EvidenceMap boundary={boundary} images={images} className="h-96 w-full" />
        {hasTimelapse ? (
          <div className="flex items-center gap-3 border-t border-border px-5 py-4">
            <button
              type="button"
              onClick={() => setPlaying((p) => !p)}
              aria-label={playing ? "Pause timelapse" : "Play timelapse"}
              className="shrink-0 rounded-full border border-border px-3 py-1 text-xs font-medium text-ink hover:bg-surface"
            >
              {playing ? "Pause" : "Play"}
            </button>
            <input
              type="range"
              min={0}
              max={frames.length - 1}
              step={1}
              value={safeIndex}
              onChange={(e) => {
                setPlaying(false);
                setIndex(Number(e.target.value));
              }}
              className="h-1.5 flex-1 accent-accent"
              aria-label="Scrub the satellite timelapse"
            />
            <span className="w-24 shrink-0 text-right font-mono text-xs tabular-nums text-ink">
              {formatDate(current?.date)}
            </span>
            <span className="shrink-0 font-mono text-xs tabular-nums text-faint">
              {safeIndex + 1}/{frames.length}
            </span>
          </div>
        ) : (
          captionLayer && (
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 border-t border-border px-5 py-3 text-xs">
              <span className="label">{frames.length ? "Latest capture" : "Reference imagery"}</span>
              <span className="text-ink">{captionLayer.source ?? captionLayer.label}</span>
              {captionLayer.date && (
                <span className="font-mono tabular-nums text-muted">
                  {formatDate(captionLayer.date)}
                </span>
              )}
            </div>
          )
        )}
      </Card>

      <Card>
        <CardHeader
          title="Dated snapshots"
          action={<span className="text-xs text-muted">{series.length} in series</span>}
        />
        {series.length > 0 ? (
          <ol className="px-5 py-4">
            {series.map((s, i) => (
              <li key={i} className="flex gap-4">
                <div className="flex flex-col items-center" aria-hidden>
                  <span className="mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full border-2 border-surface bg-accent" />
                  {i < series.length - 1 && <span className="w-px flex-1 bg-border" />}
                </div>
                <div className="flex-1 pb-6 last:pb-0">
                  <p className="font-mono text-xs tabular-nums text-faint">{formatDate(s.date)}</p>
                  <p className="mt-1.5 text-sm leading-relaxed text-ink">{s.note}</p>
                  <div className="mt-2 flex flex-wrap gap-4 text-xs text-muted">
                    <span>
                      {typeConfig.footprintLabel}:{" "}
                      <span className="font-mono tabular-nums text-ink">
                        {formatNumber(s.footprint_ha, { unit: "ha" })}
                      </span>
                    </span>
                    {s.ndvi != null && (
                      <span>
                        NDVI: <span className="font-mono tabular-nums text-ink">{s.ndvi.toFixed(2)}</span>
                      </span>
                    )}
                    {s.trace?.source && <span className="text-faint">{s.trace.source}</span>}
                  </div>
                </div>
              </li>
            ))}
          </ol>
        ) : (
          <div className="px-5 py-12 text-center text-sm text-muted">
            No dated snapshots recorded yet.
          </div>
        )}
      </Card>
    </div>
  );
}
