"use client";
import { use } from "react";
import { ConfidenceRating } from "@/components/features/ConfidenceRating";
import { Card, CardBody, CardHeader, CardSkeleton } from "@/components/ui/Card";
import { Disclosure } from "@/components/ui/Disclosure";
import { RiskBar } from "@/components/ui/RiskMeter";
import { Badge } from "@/components/ui/Badge";
import { Stat } from "@/components/ui/Stat";
import { TraceChip } from "@/components/features/TraceChip";
import { DossierUnavailable } from "@/components/features/DossierUnavailable";
import { MetricLabel, ScaleCue } from "@/components/ui/MetricInfo";
import { METRICS, scaleLine, type MetricKey } from "@/lib/metrics";
import { formatNumber, formatPercent, riskTone, titleCase, TONE_BG, type RiskTone } from "@/lib/format";
import { useDossier } from "@/lib/queries";
import type { HazardScore } from "@/lib/types";

/** Score + band rows, shared by both materiality cards so the two directions are read on
 * the same scale — the point is that they are comparable but never combined.
 *
 * The scale is stated once in the footer rather than per row, and only when the scored rows
 * genuinely agree on one: the list also carries rows the pipeline does not score (heat, water
 * stress), and a footer asserting a scale over those would be describing numbers that aren't
 * there. Each row's own trigger carries what that hazard measures. */
function HazardList({ rows }: { rows: ReadonlyArray<readonly [MetricKey, HazardScore]> }) {
  // Agree by rendered line, not object identity: two value-equal scales should still count as
  // one, so the footer survives a scale being written as its own literal rather than the
  // shared constant.
  const scaled = rows.map(([m]) => METRICS[m].scale).filter((s) => s !== undefined);
  const shared = new Set(scaled.map(scaleLine)).size === 1 ? scaled[0] : null;
  return (
    <div>
      <ul className="space-y-2.5">
        {rows.map(([metric, h]) => (
          <li
            key={metric}
            className="flex items-center justify-between gap-4 text-sm last:border-t last:border-border last:pt-2.5 last:font-medium"
          >
            {/* The footer below states the scale once for the whole list, so the row
                tooltips don't repeat it. */}
            <MetricLabel metric={metric} labelClassName="text-ink" showScale={!shared} />
            <span className="flex items-center gap-3">
              <span className="font-mono tabular-nums text-muted">{h.score ?? "—"}</span>
              {h.band && <Badge tone={riskTone(h.band)}>{h.band}</Badge>}
            </span>
          </li>
        ))}
      </ul>
      {shared && (
        <p className="mt-4 border-t border-border pt-3 font-mono text-xs text-faint">
          {scaleLine(shared)}
        </p>
      )}
    </div>
  );
}

/** A driver reads as a slip/risk if it names a schedule or scope shortfall; otherwise it's
 * corroborating. Purely a display heuristic over the rationale text — drivers[] is a list of
 * strings, not scored, so this only orders/colors the row, it doesn't recompute anything. */
function driverSentiment(text: string): RiskTone {
  return /slip|risk|behind|variance|delay|shortfall|below target|miss/i.test(text)
    ? "medium"
    : "low";
}

/** Step 5 of the narrative — "the product": the headline on-track confidence %, the
 * rationale, and the drivers that produced it, plus the underlying risk score. */
export default function Confidence({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: dossier, isLoading, isError, error } = useDossier(id);

  if (isError) return <DossierUnavailable error={error} noun="confidence" />;
  if (isLoading || !dossier) return <CardSkeleton />;

  const { confidence, physical_risk: pr, environmental_effect: ee, impact: imp } = dossier;
  const band = riskTone(confidence.risk_band);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader
          title={<MetricLabel metric="onTrackConfidence" />}
          action={<TraceChip traces_to={confidence.trace?.traces_to} />}
        />
        <CardBody className="space-y-5">
          {/* The two headline figures run in opposite directions on the same colour ramp, so
              each states its own direction rather than leaving the reader to infer it. */}
          <div className="flex flex-wrap items-center justify-between gap-6">
            <div>
              <ConfidenceRating pct={confidence.on_track_pct} band={confidence.risk_band} />
              <ScaleCue metric="onTrackConfidence" className="mt-3 block" />
            </div>
            <div className="text-right">
              <MetricLabel metric="riskScore" className="mb-1" labelClassName="label" />
              <p className="font-mono text-3xl font-semibold leading-none tabular-nums text-ink">
                {confidence.risk_score ?? "—"}
                {/* Denominator only when there's a numerator — otherwise a missing score would
                    read as "—/100", a dash measured out of 100. */}
                {confidence.risk_score != null && (
                  <span className="text-lg font-normal text-faint">
                    /{METRICS.riskScore.scale?.max}
                  </span>
                )}
              </p>
              <RiskBar score={confidence.risk_score} tone={band} className="mt-2 w-32" />
              <ScaleCue metric="riskScore" className="mt-2 block" />
            </div>
          </div>
          {/* Short generic lead-in, always visible; the long per-asset assessment folds away
              below it so the card stays compact until someone wants the detail. */}
          <p className="border-t border-border pt-4 text-sm leading-relaxed text-muted">
            The one rating the review acts on: how on-track this asset is against its disclosed
            claims, with the risk score beside it and the signals that produced it. The rating
            traces back to the evidence on the prior screens.
          </p>
          {confidence.rationale && (
            <Disclosure
              className="border-t border-border pt-4"
              summaryClassName="text-sm font-medium text-ink"
              bodyClassName="pt-3"
              summary="What this rating means"
            >
              <p className="text-[15px] leading-relaxed text-ink">{confidence.rationale}</p>
            </Disclosure>
          )}
        </CardBody>
      </Card>

      <Card>
        <CardHeader
          title="Drivers"
          action={<span className="text-xs text-muted">Signals behind the rating</span>}
        />
        <CardBody>
          <ul className="space-y-3">
            {confidence.drivers.map((d, i) => (
              <li key={i} className="flex gap-3">
                <span
                  className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${TONE_BG[driverSentiment(d)]}`}
                  aria-hidden
                />
                <p className="text-sm text-ink">{d}</p>
              </li>
            ))}
          </ul>
        </CardBody>
      </Card>

      {/* Double materiality: the two directions are asked, scored and shown separately —
          the reason why is on screen now, in METRICS.effectComposite. */}
      {(pr || ee) && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {pr && (
            <Card>
              <CardHeader
                title="Risk to the asset"
                action={<span className="text-xs text-muted">What nature does to it</span>}
              />
              <CardBody>
                <HazardList
                  rows={[
                    ["fire", pr.fire],
                    ["flood", pr.flood],
                    ["heat", pr.heat],
                    ["waterStress", pr.water_stress],
                    ["hazardComposite", pr.composite],
                  ]}
                />
              </CardBody>
            </Card>
          )}
          {ee && (
            <Card>
              <CardHeader
                title="Impact on the environment"
                action={<span className="text-xs text-muted">What it does to nature</span>}
              />
              <CardBody className="space-y-4">
                <HazardList
                  rows={[
                    ["vegetationLoss", ee.vegetation_loss],
                    ["effectComposite", ee.composite],
                  ]}
                />
                {(ee.land_disturbance_ha != null || ee.water_change_pct != null) && (
                  <div className="grid grid-cols-2 gap-4 border-t border-border pt-4">
                    {ee.land_disturbance_ha != null && (
                      <Stat
                        metric="landDisturbance"
                        value={formatNumber(ee.land_disturbance_ha, { unit: "ha" })}
                      />
                    )}
                    {ee.water_change_pct != null && (
                      <Stat metric="waterChange" value={formatPercent(ee.water_change_pct)} />
                    )}
                  </div>
                )}
              </CardBody>
            </Card>
          )}
        </div>
      )}

      {imp && (
        <Card>
          <CardHeader
            title="Impact"
            action={<span className="text-xs text-muted">Modeled figures</span>}
          />
          <CardBody className="space-y-4">
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
              {imp.generation_gwh != null && (
                <Stat
                  metric="generation"
                  value={formatNumber(imp.generation_gwh, { unit: "GWh/yr" })}
                />
              )}
              {imp.avoided_emissions_tco2 != null && (
                <Stat
                  metric="avoidedEmissions"
                  value={formatNumber(imp.avoided_emissions_tco2, { unit: "tCO2e/yr" })}
                />
              )}
              {imp.carbon_stock_tco2 != null && (
                <Stat
                  metric="carbonStock"
                  value={formatNumber(imp.carbon_stock_tco2, { unit: "tCO2e" })}
                  sub={imp.carbon_band ?? undefined}
                />
              )}
              {imp.co2_intensity_value != null && (
                <Stat
                  metric="co2Intensity"
                  value={formatNumber(imp.co2_intensity_value, { unit: imp.co2_intensity_unit ?? "" })}
                />
              )}
              {imp.assurance && <Stat metric="assurance" value={imp.assurance} />}
            </div>
            {imp.build_year != null && imp.financing_year != null && (
              <div className="flex flex-wrap items-center gap-2 border-t border-border pt-3 text-sm">
                <MetricLabel metric="additionality" labelClassName="label" />
                <span className="text-muted">
                  Built {imp.build_year}, financed {imp.financing_year}
                </span>
                {imp.additionality_verdict && (
                  <Badge tone={imp.additionality_verdict === "consistent" ? "low" : "medium"}>
                    {titleCase(imp.additionality_verdict)}
                  </Badge>
                )}
              </div>
            )}
          </CardBody>
        </Card>
      )}
    </div>
  );
}
