"""Evidence-graph node schema (WI-4).

Every value in a verification lives as a node that traces back to the base
disclosure. Node types:
  - source      : an external dataset (GEM, OSM, Sentinel, ERA5) or the disclosure
  - claim       : something the disclosure *asserts* (capacity, area, CO2, ...)
  - observation : something we measured from EO / reference data
  - derived     : something computed (generation, avoided emissions) — carries the
                  formula used and an assurance label

The invariant (enforced in graph_builder.validate_graph): every node has a path
back to the disclosure root — no orphan numbers.
"""

NODE_TYPES = {"source", "claim", "observation", "derived"}
ASSURANCE = {"observed", "modelled", "needs-ground-truth", "disclosed"}


def make_node(node_id, node_type, value, *, unit=None, source=None, source_url=None,
              method=None, confidence=None, formula_at_time=None,
              assurance_label=None, date=None, parent_ids=None, inputs=None,
              verdict=None):
    """Build one schema-valid node dict. `parent_ids` are the edges toward root."""
    assert node_type in NODE_TYPES, f"bad node type {node_type}"
    if assurance_label is not None:
        assert assurance_label in ASSURANCE, f"bad assurance {assurance_label}"
    node = {
        "id": node_id, "type": node_type, "value": value, "unit": unit,
        "source": source, "source_url": source_url, "method": method,
        "confidence": confidence, "formula_at_time": formula_at_time,
        "assurance_label": assurance_label, "date": date,
        "parent_ids": list(parent_ids or []), "inputs": list(inputs or []),
        "verdict": verdict,
    }
    return {k: v for k, v in node.items()
            if v is not None or k in ("parent_ids", "inputs")}
