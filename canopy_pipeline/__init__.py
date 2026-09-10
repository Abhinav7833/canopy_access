"""Canopy geospatial engine.

Production-grade §4.1 module layout, all computed in Google Earth Engine.
Public API:
    init_ee()       -> connect to Earth Engine
    run_pipeline()  -> run the full analysis on one request

Resolved lazily so that importing a submodule does not pull in Earth Engine. Several
modules here are pure Python (risk_scoring, confidence, cross_check, screening) and are
worth importing — and testing — on a machine with no GEE credentials and no `ee`
installed; the eager import made that impossible. `from canopy_pipeline import
run_pipeline` behaves exactly as before, it just resolves on first use (PEP 562).
"""

__all__ = ["init_ee", "run_pipeline"]


def __getattr__(name: str):
    if name == "init_ee":
        from .session import init_ee

        return init_ee
    if name == "run_pipeline":
        from .run_pipeline import run_pipeline

        return run_pipeline
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
