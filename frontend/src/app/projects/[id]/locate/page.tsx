"use client";
import { use } from "react";
import { EvidenceMap, type MapImage } from "@/components/map/EvidenceMap";
import { Badge } from "@/components/ui/Badge";
import { Card, CardBody, CardHeader, CardSkeleton } from "@/components/ui/Card";
import { RiskBar } from "@/components/ui/RiskMeter";
import { TraceChip } from "@/components/features/TraceChip";
import { DossierUnavailable } from "@/components/features/DossierUnavailable";
import { MetricLabel, ScaleCue } from "@/components/ui/MetricInfo";
import { confidenceValueTone, formatNumber, formatPercent } from "@/lib/format";
import { referenceFrame } from "@/lib/imagery";
import { useBoundary, useDossier, useImagery } from "@/lib/queries";

/** Step 2 of the narrative: the claimed region resolved to a located asset, shown on real
 * satellite imagery of the AOI with the located boundary drawn on top. Nothing downstream
 * (observe, cross-check, confidence) means anything if the asset is misidentified, so this
 * screen also shows what was ruled out and why. */
export default function Locate({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: boundary, isError: boundaryError, error: boundaryErr } = useBoundary(id);
  const { data: imagery } = useImagery(id);
  const { data: dossier, isLoading, isError: dossierError, error: dossierErr } = useDossier(id);

  if (boundaryError || dossierError)
    return <DossierUnavailable error={dossierErr ?? boundaryErr} noun="localization" />;
  if (isLoading || !dossier || !boundary) return <CardSkeleton />;

  const { localization } = dossier;
  const [lon, lat] = localization.located_centroid;
  const tone = confidenceValueTone(localization.confidence);

  // Real AOI imagery, served from the app's own backend, so the located asset is shown on
  // real satellite pixels rather than an abstraction of them.
  const aoi = referenceFrame(imagery);
  const images: MapImage[] = aoi ? [{ id: "aoi", url: aoi.url, opacity: 1 }] : [];
  const areaHa = boundary.properties.area_hectares;

  return (
    <div className="space-y-6">
      <p className="text-sm text-muted">
        The claimed region, resolved to one located asset. Nothing downstream (the imagery, the
        cross-checks, the confidence rating) holds if this match is wrong, so the candidates ruled
        out are shown alongside it.
      </p>
      <Card>
        <CardHeader
          title="Located asset"
          action={<span className="text-xs text-muted">Claimed region → AOI match</span>}
        />
        <EvidenceMap boundary={boundary} images={images} marker={{ lon, lat }} className="h-96 w-full" />
        <div className="border-t border-border px-5 py-3">
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs">
            <span className="label">AOI extent</span>
            {areaHa != null && (
              <span className="font-mono tabular-nums text-ink">
                {formatNumber(areaHa, { unit: "ha" })}
              </span>
            )}
            <span className="font-mono tabular-nums text-muted">
              {lat.toFixed(4)}, {lon.toFixed(4)}
            </span>
            {/* Stated here rather than left to be inferred from the fact that a polygon
                exists — see METRICS.aoiAssurance for what it governs. */}
            {localization.aoi_assurance && (
              <MetricLabel metric="aoiAssurance" labelClassName="text-muted">
                {localization.aoi_assurance}
              </MetricLabel>
            )}
          </div>
          {/* The AOI is the analysed region, deliberately larger than the disclosed asset. Say
              so next to the figure so the larger number doesn't read as over-measurement. */}
          {areaHa != null && (
            <p className="mt-1.5 text-xs text-muted">
              Larger than the disclosed asset, which sits within it — this is the region
              analysed, not the asset&apos;s own footprint.
            </p>
          )}
        </div>
      </Card>

      <Card>
        <CardHeader
          title="Localization"
          action={<TraceChip traces_to={localization.trace?.traces_to} />}
        />
        <CardBody className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <p className="label mb-1">Region hint (disclosed)</p>
              <p className="text-sm text-ink">{localization.region_hint}</p>
            </div>
            <div>
              <p className="label mb-1">Located centroid</p>
              <p className="font-mono text-sm tabular-nums text-ink">
                {lat.toFixed(4)}, {lon.toFixed(4)}
              </p>
            </div>
          </div>

          <div>
            <div className="mb-1.5 flex items-center justify-between text-sm">
              <MetricLabel metric="localizationConfidence" labelClassName="text-ink" />
              <Badge tone={tone}>{formatPercent(localization.confidence, true)}</Badge>
            </div>
            <RiskBar score={Math.round(localization.confidence * 100)} tone={tone} />
            {/* Reads on the opposite polarity to the risk scores elsewhere in the dossier,
                so it says so rather than relying on the shared colour ramp. */}
            <ScaleCue metric="localizationConfidence" className="mt-2 block" />
          </div>

          <p className="border-t border-border pt-3 text-xs text-muted">{localization.method}</p>
        </CardBody>
      </Card>

      {localization.alternatives_rejected.length > 0 && (
        <Card>
          <CardHeader
            title="Candidates ruled out"
            action={<span className="text-xs text-muted">Why this AOI, and not the alternatives</span>}
          />
          <CardBody>
            <ul className="space-y-3">
              {localization.alternatives_rejected.map((a, i) => (
                <li key={i} className="flex gap-3">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-faint" aria-hidden />
                  <p className="text-sm text-muted">
                    <span className="font-medium text-ink">{a.name}</span>: {a.reason}
                  </p>
                </li>
              ))}
            </ul>
          </CardBody>
        </Card>
      )}
    </div>
  );
}
