"""Run the Canopy pipeline on the demo projects.

Usage:
    # one-time browser auth (per machine):
    python -c "import ee; ee.Authenticate()"

    python run_demo.py                # default: mikoko (mangrove)
    python run_demo.py nur_navoi      # solar
    python run_demo.py both           # run both, one after the other
"""

import json
import sys

from canopy_pipeline import init_ee, run_pipeline
from canopy_pipeline.examples import EXAMPLES

if __name__ == "__main__":
    init_ee()
    which = sys.argv[1] if len(sys.argv) > 1 else "mikoko"

    names = list(EXAMPLES) if which == "both" else [which]
    for name in names:
        print("=" * 72)
        print(name)
        print("=" * 72)
        result = run_pipeline(EXAMPLES[name], export=False)
        print(json.dumps(result, indent=2, default=str))
