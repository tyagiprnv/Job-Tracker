"""Manage job applications in Google Sheets."""

from datetime import datetime
from typing import Optional

from sheets.client import SheetsClient
from models.application import Application
from models.email import Email
from config.settings import TERMINAL_STATUSES, STATUS_VALUES
from detection.false_positives import FalsePositivesTracker
from tracking.processed_emails import ProcessedEmailsTracker


class ApplicationManager:
    """Manage job applications in Google Sheets."""

    def __init__(self, spreadsheet_id: Optional[str] = None):
        """Initialize application manager.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
        """
        self.client = SheetsClient(spreadsheet_id) if spreadsheet_id else SheetsClient()
        self.client.open_spreadsheet()
        self.false_positives = FalsePositivesTracker()
        self.processed_emails = ProcessedEmailsTracker()

    def get_all_applications(self) -> list[Application]:
        """Get all applications from sheet.

        Returns:
            list: List of Application objects
        """
        rows = self.client.get_all_rows()

        # Skip header row
        applications = []
        for i, row in enumerate(rows[1:], start=2):
            if row and row[0]:  # Skip empty rows
                try:
                    app = Application.from_row(row, row_number=i)
                    applications.append(app)
                except Exception as e:
                    print(f"Error parsing row {i}: {e}")
                    continue

        return applications

    def create_application(self, email: Email) -> Optional[Application]:
        """Create new application from email.

        Args:
            email: Email object with extracted info

        Returns:
            Application: Created application object, or None if false positive or already processed
        """
        # Check if this email was already processed
        if self.processed_emails.is_processed(email.message_id):
            print(
                f"Skipping already processed email: {email.company} - {email.position} "
                f"(message: {email.message_id[:8]}...)"
            )
            return None

        # Check if this is a known false positive
        if self.false_positives.is_false_positive(
            email.message_id, email.company or "Unknown", email.position or "Unknown Position"
        ):
            print(
                f"Skipping false positive: {email.company} - {email.position} "
                f"(previously deleted by user)"
            )
            return None

        application = Application(
            company=email.company or "Unknown",
            position=email.position or "Unknown Position",
            application_date=email.date,
            current_status=email.status or "Applied",
            last_updated=email.date,
            email_count=1,
            latest_email_date=email.date,
            notes="",
            gmail_link=email.gmail_link,
            thread_id=email.thread_id,
        )

        # Add to sheet
        self.client.append_row(application.to_row())

        # Mark email as processed
        self.processed_emails.mark_processed(email.message_id)

        print(f"Created: {application.company} - {application.position}")

        return application

    def update_application(self, application: Application, email: Email) -> bool:
        """Update existing application with new email.

        Args:
            application: Existing application
            email: New email

        Returns:
            bool: True if update was performed, False if skipped
        """
        # Check if this email was already processed
        if self.processed_emails.is_processed(email.message_id):
            print(
                f"Skipping already processed email: {application.company} - {application.position} "
                f"(message: {email.message_id[:8]}...)"
            )
            return False

        # Re-find the application to get current row number and fresh data
        # (in case rows were manually deleted/reordered)
        current_app = self._find_application_by_identity(application)

        if not current_app:
            # Application was manually deleted - record as false positive
            print(
                f"Warning: {application.company} - {application.position} was manually deleted. "
                f"Recording as false positive (won't be re-created)."
            )
            self.false_positives.add_false_positive(
                email.message_id,
                application.company,
                application.position,
            )
            # Mark as processed so we don't keep trying
            self.processed_emails.mark_processed(email.message_id)
            return False

        # Work with fresh data from spreadsheet (current_app)
        # IMPORTANT: Preserve application_date and ensure it's the EARLIEST date
        if email.date < current_app.application_date:
            # This email is earlier than our current application date - update to earliest
            current_app.application_date = email.date

        # Check if status should be updated
        new_status = email.status
        current_status = current_app.current_status

        # Determine if status update is allowed
        should_update_status = (
            current_status not in TERMINAL_STATUSES
            and self._should_update_status(current_status, new_status)
        )

        if should_update_status:
            # Update status
            current_app.current_status = new_status
            print(f"Updating status for {current_app.company}: {current_status} -> {new_status}")
        else:
            # Status update not allowed (terminal or downgrade)
            if current_status in TERMINAL_STATUSES:
                print(
                    f"Preserving terminal status for {current_app.company}: {current_status} "
                    f"(not updating to {new_status})"
                )
            else:
                print(
                    f"Preserving status for {current_app.company}: {current_status} "
                    f"(would downgrade to {new_status})"
                )

        # Always update metadata (regardless of status update)
        current_app.email_count += 1
        current_app.latest_email_date = max(email.date, current_app.latest_email_date or email.date)
        current_app.last_updated = email.date
        if email.gmail_link:
            current_app.gmail_link = email.gmail_link

        # Update in sheet using current row number
        if current_app.row_number:
            self.client.update_row(current_app.row_number, current_app.to_row())
            print(
                f"Updated: {current_app.company} - {current_app.position} -> {current_app.current_status}"
            )

        # Mark email as processed
        self.processed_emails.mark_processed(email.message_id)

        return True

    def _should_update_status(self, current: str, new: str) -> bool:
        """Check if status should be updated.

        Args:
            current: Current status
            new: New status

        Returns:
            bool: True if should update
        """
        # Terminal statuses should not be updated
        if current in TERMINAL_STATUSES:
            return False

        # If new status is not in STATUS_VALUES, don't update
        if new not in STATUS_VALUES:
            return False

        # Get status indices
        try:
            current_idx = STATUS_VALUES.index(current)
            new_idx = STATUS_VALUES.index(new)

            # Only update if new status is forward progress or same
            return new_idx >= current_idx
        except ValueError:
            # If status not found in list, allow update
            return True

    def find_application(
        self, company: str, position: str
    ) -> Optional[Application]:
        """Find application by company and position.

        Args:
            company: Company name
            position: Position title

        Returns:
            Application: Found application or None
        """
        applications = self.get_all_applications()

        for app in applications:
            if app.company.lower() == company.lower() and app.position.lower() == position.lower():
                return app

        return None

    def _find_application_by_identity(
        self, application: Application
    ) -> Optional[Application]:
        """Re-find application in current spreadsheet state.

        Uses thread_id (if available) or company+position to locate the application.
        This ensures we get the current row number even if rows were manually changed.

        Args:
            application: Application to find

        Returns:
            Application: Found application with current row number, or None if deleted
        """
        # Re-read spreadsheet to get current state
        current_apps = self.get_all_applications()

        # Try to match by thread_id first (most reliable)
        if application.thread_id:
            for app in current_apps:
                if app.thread_id == application.thread_id:
                    return app

        # Fall back to company + position match
        for app in current_apps:
            if (
                app.company.lower() == application.company.lower()
                and app.position.lower() == application.position.lower()
            ):
                return app

        # Application not found (may have been manually deleted)
        return None
