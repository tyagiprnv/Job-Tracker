"""Detect conflicts between spreadsheet and email data."""

from typing import Optional, Literal
from dataclasses import dataclass

from models.application import Application
from models.email import Email


@dataclass
class FieldConflict:
    """Represents a conflict for a single field."""

    field_name: str  # "Company" or "Position"
    spreadsheet_value: str
    email_value: str
    is_upgrade: bool  # Unknown → real value


def is_unknown_value(
    value: Optional[str], field_type: Literal["company", "position"]
) -> bool:
    """Check if a value is considered unknown.

    Args:
        value: The value to check
        field_type: Type of field ("company" or "position")

    Returns:
        bool: True if value is unknown
    """
    if field_type == "position":
        return value in [None, "", "Unknown", "Unknown Position"]
    elif field_type == "company":
        return value in [None, "", "Unknown"]
    return False


def detect_field_conflict(
    spreadsheet_value: str,
    email_value: str,
    field_type: Literal["company", "position"],
) -> Optional[FieldConflict]:
    """Detect conflict for a single field.

    Args:
        spreadsheet_value: Current value in spreadsheet
        email_value: New value from email
        field_type: Type of field ("company" or "position")

    Returns:
        FieldConflict if there's a conflict or upgrade needed, None otherwise
    """
    ss_unknown = is_unknown_value(spreadsheet_value, field_type)
    email_unknown = is_unknown_value(email_value, field_type)

    # Case 1: Both unknown or same value → no conflict
    if spreadsheet_value == email_value:
        return None

    # Case 2: Upgrade (unknown → real)
    if ss_unknown and not email_unknown:
        field_name = "Company" if field_type == "company" else "Position"
        return FieldConflict(
            field_name=field_name,
            spreadsheet_value=spreadsheet_value,
            email_value=email_value,
            is_upgrade=True,
        )

    # Case 3: Downgrade (real → unknown) - block but don't conflict
    if not ss_unknown and email_unknown:
        return None  # Silently preserve spreadsheet value

    # Case 4: Both real but different → conflict
    if not ss_unknown and not email_unknown:
        field_name = "Company" if field_type == "company" else "Position"
        return FieldConflict(
            field_name=field_name,
            spreadsheet_value=spreadsheet_value,
            email_value=email_value,
            is_upgrade=False,
        )

    return None


def detect_conflicts(application: Application, email: Email) -> list[FieldConflict]:
    """Detect all conflicts between spreadsheet and email.

    Args:
        application: Existing spreadsheet application
        email: Incoming email with potentially different values

    Returns:
        List of FieldConflict objects (empty if no conflicts)
    """
    conflicts = []

    # Check company
    company_conflict = detect_field_conflict(
        application.company, email.company or "Unknown", "company"
    )
    if company_conflict:
        conflicts.append(company_conflict)

    # Check position
    position_conflict = detect_field_conflict(
        application.position, email.position or "Unknown Position", "position"
    )
    if position_conflict:
        conflicts.append(position_conflict)

    return conflicts
