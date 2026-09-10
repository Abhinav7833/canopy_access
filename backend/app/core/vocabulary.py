"""Controlled vocabularies of the pipeline spec.

Defined here rather than in `models` or `schemas` because all three layers need the same
words: the storage layer constrains them, the wire contract publishes them, and the seeder
validates fixtures against them. One definition, so the layers cannot drift apart.
"""

from typing import Literal, get_args

# A cross-check either agrees with the claim, agrees on the part the observation can reach,
# contradicts it, or cannot judge it.
CrossCheckStatus = Literal[
    "consistent", "partially_consistent", "inconsistent", "insufficient_data"
]
CROSS_CHECK_STATUSES: tuple[str, ...] = get_args(CrossCheckStatus)

# What a legal cross-reference interrogates. A legal check is a cross-check like any other
# — it reuses `CrossCheckStatus`, so a clean register reads `consistent`, a disclosure-only
# assertion `partially_consistent`, a sanctions hit or revoked permit `inconsistent`, and an
# unreachable register `insufficient_data` rather than a reassuring silence.
LegalCheckType = Literal["permit", "sanction", "litigation", "ownership"]
LEGAL_CHECK_TYPES: tuple[str, ...] = get_args(LegalCheckType)
