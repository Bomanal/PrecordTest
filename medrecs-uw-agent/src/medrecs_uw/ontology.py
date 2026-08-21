"""Canonical names from the Precord package.

context/ontology_nodes.csv is the naming authority but is not shipped in this
package. Names below are taken from schemas/case.schema.json and the agent
prompts' domain packs.
"""

from __future__ import annotations

UNDERWRITING_CASE_ID = "underwriting_case_id"
ATTENDING_PHYSICIAN_STATEMENT = "attending_physician_statement"
LABORATORY_REPORT = "laboratory_report"
FACE_AMOUNT = "face_amount"
CYCLE_TIME = "cycle_time"
UNDERWRITING_DECISION = "underwriting_decision"
RISK_CLASSIFICATION = "risk_classification"
STATUS_IN_REVIEW = "In Review"
STATUS_CLOSED = "Closed"
STATUS_MANUAL_RECORD_REQUEST_REQUIRED = "Manual Record Request Required"

HUMAN_DECISIONS = {"refer", "postpone", "decline"}
BOUND_STATUSES = {
    "bound",
    "issued",
    "bound and issued",
    "policy issued",
    "in force",
}

# Prompt §2 "Never automate these" — used when context/ is absent.
NEVER_AUTOMATE_STEPS = {
    "S1",
    "S2",
    "S4",
    "S6",
    "S7",
    "S10",
    "S11",
    "S12",
    "S14",
}

SERVED_STEPS = {
    "BLK-REQS-CHASE": ("S3", "S8"),
    "BLK-INTAKE-MONITOR": ("S5", "S9"),
    "BLK-AUTO-ARCHIVE": ("S13",),
}
