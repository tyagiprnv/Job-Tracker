"""Human-in-the-loop conflict resolution module."""

from hitl.conflict_detector import detect_conflicts, FieldConflict
from hitl.conflict_resolver import ConflictResolver, ConflictResolution

__all__ = [
    "detect_conflicts",
    "FieldConflict",
    "ConflictResolver",
    "ConflictResolution",
]
