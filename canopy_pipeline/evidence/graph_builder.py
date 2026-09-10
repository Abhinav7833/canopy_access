"""Evidence-graph builder (WI-4).

Assembles a per-asset provenance graph from the disclosure claims, the observed
pipeline output, and the cross-check verdicts. Uses networkx in-memory; serialises
to plain JSON that export/ (and Cem's UI) can read. `validate_graph` enforces the
anti-orphan invariant: every node must trace back to the disclosure root.
"""
import networkx as nx

from .graph_schema import make_node

_SOURCES = {
    "gem": "GEM Global Solar Power Tracker (Feb-2026)",
    "osm": "OpenStreetMap footprint",
    "s2": "Sentinel-2 (optical)",
    "s1": "Sentinel-1 (radar)",
    "era5": "ERA5-Land (weather / GHI)",
}


def _add(g, node):
    g.add_node(node["id"], **node)
    for p in node.get("parent_ids", []):
        g.add_edge(node["id"], p)   # edge points toward root
    return node["id"]


def build_graph(asset_id, claims, observed, checks):
    """Return (DiGraph, root_id). Edges point from a node toward the root."""
    g = nx.DiGraph()
    root = f"{asset_id}.disclosure.root"
    _add(g, make_node(root, "source", "base disclosure",
                       source=claims.get("name"), assurance_label="disclosed"))
    for k, label in _SOURCES.items():
        _add(g, make_node(f"{asset_id}.source.{k}", "source", label, parent_ids=[root]))

    # --- claims (attach to root) ---
    claim_id = {}
    for key, c in claims.get("claims", {}).items():
        cid = f"{asset_id}.claim.{key}"
        claim_id[key] = cid
        _add(g, make_node(cid, "claim", c.get("value"), unit=c.get("unit"),
                          source=c.get("source"), source_url=c.get("source_url"),
                          assurance_label="disclosed", parent_ids=[root]))

    verdict_of = {r["claim"]: r for r in (checks or [])}
    ev = (observed.get("evidence") or [{}])[0] if observed else {}
    gen = ev.get("generation_estimate") or {}

    def obs(name, typ, value, tests_key, sources, **kw):
        parents = [claim_id[tests_key]] if tests_key in claim_id else [root]
        v = verdict_of.get(_TEST_MAP.get(name))
        # explicit assurance_label (e.g. "modelled") wins; else take the verdict's
        kw.setdefault("assurance_label", (v or {}).get("assurance_label"))
        _add(g, make_node(f"{asset_id}.{typ}.{name}", typ, value,
                          parent_ids=parents,
                          inputs=[f"{asset_id}.source.{s}" for s in sources],
                          verdict=(v or {}).get("verdict"), **kw))

    if observed:
        # observation: footprint area (tests the area claim)
        obs("footprint_ha", "observation",
            (observed.get("metadata") or {}).get("aoi_area_hectares"),
            "area_ha", ["osm", "gem"], unit="ha",
            method="geopandas area of matched footprint")
        # observation: build onset (tests the timing/financing claim)
        obs("build_onset_year", "observation", ev.get("build_year_estimate"),
            "financing_date", ["s1"],
            method="Sentinel-1 backscatter step (|Δ| dating)")
        # derived: generation estimate (tests the generation claim)
        obs("generation_gwh", "derived",
            [gen.get("est_gwh_fixed_tilt"), gen.get("est_gwh_tracking")],
            "generation_gwh_yr", ["era5"], unit="GWh/yr",
            formula_at_time="PVWatts: capacity x GHI x PR x tracking",
            assurance_label="modelled")
        # derived: avoided emissions (tests the CO2 claim)
        obs("avoided_tco2", "derived",
            [gen.get("est_tco2_avoided_fixed"), gen.get("est_tco2_avoided_tracking")],
            "co2_avoided_tpy", ["era5"], unit="tCO2/yr",
            formula_at_time=("generation(MWh) x grid_factor "
                             f"{gen.get('grid_emission_factor_tco2_per_mwh')} "
                             f"[{gen.get('grid_emission_factor_source')}]"),
            assurance_label="modelled")
    return g, root


# which observation/derived node tests which cross_check claim record
_TEST_MAP = {
    "footprint_ha": "footprint_area_ha",
    "build_onset_year": "build_onset_vs_financing",
    "generation_gwh": "generation_gwh_yr",
    "avoided_tco2": "co2_avoided_tpy",
}


def validate_graph(g, root):
    """Return list of orphan node ids (no path to root). Empty list = valid."""
    orphans = []
    for n in g.nodes:
        if n == root:
            continue
        if not nx.has_path(g, n, root):
            orphans.append(n)
    return orphans


def to_json(g):
    """Serialise to a plain node-link dict (JSON-safe)."""
    return nx.node_link_data(g, edges="edges")
