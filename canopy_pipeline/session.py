"""Earth Engine session — one place that connects to GEE."""

import os
import ee

from . import config


def init_ee(project: str | None = None) -> str:
    """Initialize Earth Engine. Run `ee.Authenticate()` once per machine first.

    Project resolution order: explicit arg -> EE_PROJECT env var -> config.
    """
    project = project or os.environ.get("EE_PROJECT") or config.EE_PROJECT
    ee.Initialize(project=project)
    print("EE ok:", ee.String("connected").getInfo(), "| project:", project)
    return project
