"""Request validation.

Lightweight, dependency-free checks so the pipeline fails fast with a clear
message. The production backend (Cem) supplies the full Pydantic model per
spec §4.2; this mirrors its required fields for standalone runs.
"""

REQUIRED = ["analysis_id", "aoi_coords", "before", "after", "cloud_pct"]


def validate(req: dict) -> bool:
    missing = [k for k in REQUIRED if k not in req]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")
    for w in ("before", "after"):
        if not (isinstance(req[w], (list, tuple)) and len(req[w]) == 2):
            raise ValueError(f"'{w}' must be a (start_date, end_date) pair")
    return True
