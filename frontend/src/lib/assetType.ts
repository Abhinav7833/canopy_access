/** Per-asset-type presentation rules (Approach A). The "what each type looks like" config
 * lives in the frontend, keyed by the project's `asset_type`; the backend only stores the
 * type plus the dossier data. This lets a solar plant and a mangrove forest each read in
 * their own vocabulary without standing up a backend metric-definition service. */

export type AssetTypeConfig = {
  observeTitle: string; // Observe-tab CardHeader title
  footprintLabel: string; // per-snapshot area metric label
  claimLabels: Record<string, string>; // claim kind -> label, overriding the generic map
};

const DEFAULT_CONFIG: AssetTypeConfig = {
  observeTitle: "Build progress",
  footprintLabel: "Footprint",
  claimLabels: {},
};

export const ASSET_TYPES: Record<string, AssetTypeConfig> = {
  solar: {
    observeTitle: "Build progress",
    footprintLabel: "Footprint",
    claimLabels: {
      capacity_mw: "Nameplate capacity",
      generation_gwh: "Annual generation",
      co2_avoided_tpy: "CO₂ avoided",
      area_ha: "Panel-field footprint",
      cod_date: "Commercial operation date",
    },
  },
  mangrove: {
    observeTitle: "Forest change & canopy",
    footprintLabel: "Canopy area",
    claimLabels: {
      protected_ha: "Protected area",
      restored_ha: "Restored area",
      credits_tco2: "Carbon credits issued",
      community_usd: "Community benefit",
    },
  },
};

/** Resolve a type's presentation config, falling back to a safe default for an unknown or
 * still-loading type. */
export function assetTypeConfig(assetType: string | undefined): AssetTypeConfig {
  return (assetType && ASSET_TYPES[assetType]) || DEFAULT_CONFIG;
}
