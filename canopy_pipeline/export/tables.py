"""Auto-generate verification tables from the pipeline's OWN output.

This is the fix for doc↔code drift. Instead of hand-typing numbers into Word (and
letting them rot), we read the evidence bundle produced by
`verify_disclosure` + `build_graph` and emit the table directly. Every value in the
table carries the source it came from (pulled from the evidence graph), so the
document literally cannot disagree with the pipeline — one source of truth.
"""

# which cross-check claim maps to which evidence-graph node
_TEST_TO_NODE = {
    "footprint_area_ha": "observation.footprint_ha",
    "build_onset_vs_financing": "observation.build_onset_year",
    "generation_gwh_yr": "derived.generation_gwh",
    "co2_avoided_tpy": "derived.avoided_tco2",
}


def _node_index(bundle):
    return {n["id"]: n for n in bundle["evidence_graph"]["nodes"]}


def _source_of(node, idx):
    """Human-readable source of an observed/derived value: its own `source`, else
    the labels of its input source-nodes (GEM / OSM / Sentinel / ERA5)."""
    if node.get("source"):
        return node["source"]
    labels = [idx.get(i, {}).get("value") for i in node.get("inputs", [])]
    return "; ".join(str(s) for s in labels if s) or "—"


def verification_markdown(bundle: dict) -> str:
    """Render one asset's verification as a fully-sourced markdown table."""
    idx = _node_index(bundle)
    aid, r, aoi = bundle["asset_id"], bundle["resolution"], bundle.get("aoi", {})
    out = [
        f"### {bundle['name']} — verification (auto-generated from pipeline output)",
        "",
        f"Resolved to GEM `{r.get('gem_location_id')}` · match {r.get('match_score')} "
        f"({r.get('confidence_label')}) · footprint {aoi.get('observed_area_ha')} ha "
        f"({aoi.get('assurance')})",
        "",
        "| Claim | Reported | Observed | Verdict | Assurance | Source of observed |",
        "|---|---|---|---|---|---|",
    ]
    for c in bundle.get("cross_check", []):
        node = idx.get(f"{aid}.{_TEST_TO_NODE.get(c['claim'], '')}", {})
        out.append(
            f"| {c['claim']} | {c['reported']} | {c['observed']} | "
            f"**{c['verdict']}** | {c.get('assurance_label') or '—'} | "
            f"{_source_of(node, idx)} |")
    out += [
        "",
        f"_Every value traces to the disclosure root; evidence-graph orphans: "
        f"{bundle.get('orphans')} (empty = fully sourced)._",
    ]
    return "\n".join(out)
