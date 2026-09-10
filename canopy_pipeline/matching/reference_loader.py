"""Reference-database loader (WI-3, Path B).

Loads the GEM structured trackers you already have on disk into a normalised
table the entity-resolver can search. GEM gives point coordinates + attributes
(capacity, phase, status, start-year, owner) — NOT footprint polygons; those are
refined later from OSM/Catastro. Deterministic, no LLM, no ML.
"""
import os
import pandas as pd

# GEM files sit at the repo root (you downloaded them).
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEM_SOLAR = os.path.join(_ROOT, "Global-Solar-Power-Tracker-February-2026.xlsx")
GEM_SOLAR_SHEET = "Utility-Scale (1 MW+)"

_COLS = {
    "Project Name": "name", "Phase Name": "phase", "Other Name(s)": "other_names",
    "Country/Area": "country", "Capacity (MW)": "capacity_mw", "Status": "status",
    "Start year": "start_year", "Operator": "operator", "Owner": "owner",
    "Latitude": "lat", "Longitude": "lon", "Location accuracy": "location_accuracy",
    "State/Province": "state", "GEM location ID": "gem_location_id",
    "GEM phase ID": "gem_phase_id",
}


def aggregate_by_plant(df):
    """Collapse phase-rows into one row per physical plant (same GEM location id).

    A big farm is listed as several phases (Pizarro = Phase 1 553 MW + Phase 3
    36 MW). A disclosure states the TOTAL, so we match against the whole plant:
    capacity = sum of phases; coords/name/owner from the largest phase; earliest
    start year; 'operating' if any phase operates."""
    if "gem_location_id" not in df.columns:
        return df
    rows = []
    for gid, g in df.groupby("gem_location_id", dropna=False):
        g = g.copy()
        prim = g.loc[g["capacity_mw"].fillna(0).idxmax()]   # largest phase
        statuses = g["status"].astype(str).str.lower()
        rows.append({
            "name": prim.get("name"), "other_names": prim.get("other_names"),
            "country": prim.get("country"), "state": prim.get("state"),
            "capacity_mw": g["capacity_mw"].fillna(0).sum(),
            "status": "operating" if statuses.eq("operating").any() else prim.get("status"),
            "start_year": g["start_year"].min(),
            "operator": prim.get("operator"), "owner": prim.get("owner"),
            "lat": prim.get("lat"), "lon": prim.get("lon"),
            "location_accuracy": prim.get("location_accuracy"),
            "gem_location_id": gid, "n_phases": len(g),
            "source": prim.get("source"),
        })
    return pd.DataFrame(rows).reset_index(drop=True)


def load_gem_solar(path=GEM_SOLAR, country=None, use_cache=True, aggregate=False):
    """Normalised GEM solar table. `country` filters (e.g. 'Spain') for speed.

    Caches a country subset to CSV next to the workbook so repeat runs are fast
    (the raw workbook is ~104k rows).
    """
    cache = None
    if country and use_cache:
        cache = os.path.join(_ROOT, f".gem_solar_{country.lower()}.csv")
        if os.path.exists(cache):
            out = pd.read_csv(cache)
            return aggregate_by_plant(out) if aggregate else out

    df = pd.read_excel(path, sheet_name=GEM_SOLAR_SHEET)
    out = df[[c for c in _COLS if c in df.columns]].rename(columns=_COLS).copy()
    out["capacity_mw"] = pd.to_numeric(out["capacity_mw"], errors="coerce")
    out["lat"] = pd.to_numeric(out["lat"], errors="coerce")
    out["lon"] = pd.to_numeric(out["lon"], errors="coerce")
    out["source"] = "GEM Global Solar Power Tracker Feb-2026"
    if country:
        out = out[out["country"].astype(str).str.contains(country, case=False, na=False)]
    out = out.reset_index(drop=True)
    if cache is not None:
        out.to_csv(cache, index=False)
    return aggregate_by_plant(out) if aggregate else out
