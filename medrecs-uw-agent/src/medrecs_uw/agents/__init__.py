from .base import AgentResult, AutomationForbidden, NEVER_AUTOMATE_STEPS
from .blk_auto_archive import run_blk_auto_archive
from .blk_intake_monitor import run_blk_intake_monitor
from .blk_reqs_chase import run_blk_reqs_chase

AGENTS = {
    "BLK-REQS-CHASE": run_blk_reqs_chase,
    "BLK-INTAKE-MONITOR": run_blk_intake_monitor,
    "BLK-AUTO-ARCHIVE": run_blk_auto_archive,
}

__all__ = [
    "AGENTS",
    "AgentResult",
    "AutomationForbidden",
    "NEVER_AUTOMATE_STEPS",
    "run_blk_auto_archive",
    "run_blk_intake_monitor",
    "run_blk_reqs_chase",
]
