/** Dossier-narrative presentation helpers — claim-kind labels and value formatting shared
 * between the Disclosure and Cross-check screens. Generic string/number/date formatting
 * still goes through lib/format.ts; this module only knows about the dossier's fixed
 * claim vocabulary (see backend/app/schemas/project.py::Dossier). */
import { assetTypeConfig } from "@/lib/assetType";
import { formatDate, formatNumber, titleCase } from "@/lib/format";
import type { ClaimKind } from "@/lib/types";

/** Generic fallback labels, used when the asset type has no override for a kind (or is
 * unknown). Per-type vocabularies live in lib/assetType.ts. */
const CLAIM_LABELS: Record<string, string> = {
  capacity_mw: "Nameplate capacity",
  area_ha: "Site area",
  cod_date: "Commercial operation date",
  timeline_months: "Construction timeline",
};

/** Label a claim kind, preferring the asset type's vocabulary (e.g. "Panel-field footprint"
 * for solar vs "Protected area" for mangrove), then the generic map, then a title-cased kind. */
export function claimLabel(kind: ClaimKind, assetType?: string): string {
  return assetTypeConfig(assetType).claimLabels[kind] ?? CLAIM_LABELS[kind] ?? titleCase(kind);
}

/** Format a claim's promised/observed value using its kind + unit. Dates render as dates;
 * numbers render with their unit; anything else (e.g. a free-text observed description)
 * passes through unchanged. */
export function formatClaimValue(kind: ClaimKind, value: number | string, unit?: string): string {
  if (kind === "cod_date" && typeof value === "string") {
    const isoDate = value.slice(0, 10);
    return /^\d{4}-\d{2}-\d{2}$/.test(isoDate) ? formatDate(isoDate) : value;
  }
  if (typeof value === "number") return formatNumber(value, { unit });
  return value;
}
