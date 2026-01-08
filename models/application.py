"""Application data model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Application:
    """Represents a job application entry in the spreadsheet."""

    company: str
    position: str
    application_date: datetime
    current_status: str
    last_updated: datetime
    email_count: int = 1
    latest_email_date: Optional[datetime] = None
    notes: str = ""
    gmail_link: str = ""

    # For tracking (not in sheet)
    row_number: Optional[int] = None  # Sheet row number
    thread_id: Optional[str] = None  # Gmail thread ID

    def to_row(self) -> list:
        """Convert application to spreadsheet row."""
        return [
            self.company,
            self.position,
            self.application_date.strftime("%Y-%m-%d"),
            self.current_status,
            self.last_updated.strftime("%Y-%m-%d"),
            str(self.email_count),
            (
                self.latest_email_date.strftime("%Y-%m-%d")
                if self.latest_email_date
                else ""
            ),
            self.notes,
            self.gmail_link,
        ]

    @classmethod
    def from_row(cls, row: list, row_number: int) -> "Application":
        """Create application from spreadsheet row."""
        # Handle potentially empty cells
        company = row[0] if len(row) > 0 else ""
        position = row[1] if len(row) > 1 else ""
        application_date_str = row[2] if len(row) > 2 else ""
        current_status = row[3] if len(row) > 3 else "Applied"
        last_updated_str = row[4] if len(row) > 4 else ""
        email_count_str = row[5] if len(row) > 5 else "1"
        latest_email_date_str = row[6] if len(row) > 6 else ""
        notes = row[7] if len(row) > 7 else ""
        gmail_link = row[8] if len(row) > 8 else ""

        # Parse dates
        try:
            application_date = datetime.strptime(application_date_str, "%Y-%m-%d")
        except (ValueError, TypeError):
            application_date = datetime.now()

        try:
            last_updated = datetime.strptime(last_updated_str, "%Y-%m-%d")
        except (ValueError, TypeError):
            last_updated = datetime.now()

        try:
            latest_email_date = (
                datetime.strptime(latest_email_date_str, "%Y-%m-%d")
                if latest_email_date_str
                else None
            )
        except (ValueError, TypeError):
            latest_email_date = None

        try:
            email_count = int(email_count_str)
        except (ValueError, TypeError):
            email_count = 1

        return cls(
            company=company,
            position=position,
            application_date=application_date,
            current_status=current_status,
            last_updated=last_updated,
            email_count=email_count,
            latest_email_date=latest_email_date,
            notes=notes,
            gmail_link=gmail_link,
            row_number=row_number,
        )

    def __str__(self) -> str:
        """String representation of application."""
        return f"{self.company} - {self.position} ({self.current_status})"
