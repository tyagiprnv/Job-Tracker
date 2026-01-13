"""Manage application merge operations."""

from typing import List, Tuple, Optional
from datetime import datetime

from sheets.client import SheetsClient
from models.application import Application
from config.settings import SPREADSHEET_ID, STATUS_VALUES, TERMINAL_STATUSES
from tracking.merged_applications import MergedApplicationsTracker


class MergeValidationError(Exception):
    """Raised when merge validation fails."""

    pass


class MergeManager:
    """Manage merging of duplicate applications."""

    def __init__(self, spreadsheet_id: Optional[str] = None):
        """Initialize merge manager.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
        """
        self.client = (
            SheetsClient(spreadsheet_id) if spreadsheet_id else SheetsClient()
        )
        self.tracker = MergedApplicationsTracker()

    def find_merge_requests(
        self, applications: List[Application]
    ) -> List[Tuple[Application, Application]]:
        """Find all applications flagged for merging.

        Args:
            applications: List of all applications

        Returns:
            list: List of (source_app, target_app) tuples
        """
        merge_pairs = []

        for app in applications:
            if not app.merge_into_row:
                continue

            try:
                target_row = int(app.merge_into_row.strip())
            except (ValueError, AttributeError):
                print(
                    f"Warning: Invalid merge target '{app.merge_into_row}' for row {app.row_number} - skipping"
                )
                continue

            # Find target application
            target_app = None
            for candidate in applications:
                if candidate.row_number == target_row:
                    target_app = candidate
                    break

            if not target_app:
                print(
                    f"Warning: Merge target row {target_row} not found for row {app.row_number} - skipping"
                )
                continue

            # Validate merge
            try:
                self._validate_merge(app, target_app, applications)
                merge_pairs.append((app, target_app))
            except MergeValidationError as e:
                print(f"Warning: {e} - skipping merge")
                continue

        return merge_pairs

    def _validate_merge(
        self, source: Application, target: Application, all_apps: List[Application]
    ):
        """Validate merge operation.

        Args:
            source: Source application
            target: Target application
            all_apps: All applications (for circular detection)

        Raises:
            MergeValidationError: If validation fails
        """
        # Check self-merge
        if source.row_number == target.row_number:
            raise MergeValidationError(
                f"Row {source.row_number} cannot merge into itself"
            )

        # Check circular merge (target also wants to merge into source)
        if target.merge_into_row:
            try:
                target_merge_row = int(target.merge_into_row.strip())
                if target_merge_row == source.row_number:
                    raise MergeValidationError(
                        f"Circular merge detected: row {source.row_number} ↔ row {target.row_number}"
                    )
            except ValueError:
                pass

        # Check chain merge (target wants to merge elsewhere)
        if target.merge_into_row and target.merge_into_row.strip():
            raise MergeValidationError(
                f"Chain merge detected: row {source.row_number} → row {target.row_number} → row {target.merge_into_row}. "
                f"Resolve target merge first."
            )

    def execute_merge(
        self, source: Application, target: Application
    ) -> Application:
        """Execute merge of source into target.

        Args:
            source: Source application (will be deleted)
            target: Target application (will be updated)

        Returns:
            Application: Updated target application
        """
        print(
            f"\n[Merge] {source.company} (row {source.row_number}) → {target.company} (row {target.row_number})"
        )

        # Merge logic

        # 1. Application Date: Keep earliest
        if source.application_date < target.application_date:
            target.application_date = source.application_date
            print(
                f"  - Updated application date to {source.application_date.strftime('%Y-%m-%d')}"
            )

        # 2. Status: Keep most progressed
        new_status = self._get_most_progressed_status(
            source.current_status, target.current_status
        )
        if new_status != target.current_status:
            target.current_status = new_status
            print(f"  - Updated status to {new_status}")

        # 3. Email Count: Sum both
        old_count = target.email_count
        target.email_count = source.email_count + target.email_count
        print(
            f"  - Combined email count: {old_count} + {source.email_count} = {target.email_count}"
        )

        # 4. Latest Email Date: Most recent
        if source.latest_email_date and (
            not target.latest_email_date
            or source.latest_email_date > target.latest_email_date
        ):
            target.latest_email_date = source.latest_email_date
            print(
                f"  - Updated latest email date to {source.latest_email_date.strftime('%Y-%m-%d')}"
            )

        # 5. Gmail Link: From most recent email
        if source.latest_email_date and target.latest_email_date:
            if (
                source.latest_email_date > target.latest_email_date
                and source.gmail_link
            ):
                target.gmail_link = source.gmail_link
                print(f"  - Updated Gmail link to source's link")
        elif source.gmail_link and not target.gmail_link:
            target.gmail_link = source.gmail_link
            print(f"  - Added Gmail link from source")

        # 6. Notes: Concatenate
        if source.notes and target.notes:
            target.notes = f"{target.notes} | {source.notes}"
            print(f"  - Concatenated notes")
        elif source.notes:
            target.notes = source.notes
            print(f"  - Added notes from source")

        # 7. Thread IDs: Combine
        source_thread_ids = source.get_thread_ids()
        target_thread_ids = target.get_thread_ids()

        for thread_id in source_thread_ids:
            if thread_id not in target_thread_ids:
                target.add_thread_id(thread_id)

        if source_thread_ids:
            print(
                f"  - Combined thread IDs: {len(source_thread_ids)} from source"
            )

        # 8. Update last_updated
        target.last_updated = datetime.now()

        # 9. Clear merge flag from target (in case it had one)
        target.merge_into_row = None

        return target

    def _get_most_progressed_status(self, status1: str, status2: str) -> str:
        """Get the most progressed status between two.

        Args:
            status1: First status
            status2: Second status

        Returns:
            str: Most progressed status
        """
        # If either is terminal, prefer terminal
        if (
            status1 in TERMINAL_STATUSES
            and status2 not in TERMINAL_STATUSES
        ):
            return status1
        if (
            status2 in TERMINAL_STATUSES
            and status1 not in TERMINAL_STATUSES
        ):
            return status2

        # If both terminal or neither terminal, use STATUS_VALUES order
        try:
            idx1 = STATUS_VALUES.index(status1)
            idx2 = STATUS_VALUES.index(status2)
            return status1 if idx1 >= idx2 else status2
        except ValueError:
            # If status not in list, prefer the one that is
            if status1 in STATUS_VALUES:
                return status1
            if status2 in STATUS_VALUES:
                return status2
            # Neither in list, keep first
            return status1

    def execute_merges(
        self, applications: List[Application], dry_run: bool = False
    ) -> Tuple[List[Application], int]:
        """Find and execute all merge operations.

        Args:
            applications: List of all applications
            dry_run: If True, preview merges without executing

        Returns:
            tuple: (updated_applications_list, num_merges_executed)
        """
        merge_pairs = self.find_merge_requests(applications)

        if not merge_pairs:
            return applications, 0

        print(f"\n[Merge] Found {len(merge_pairs)} merge request(s)")

        if dry_run:
            print("[Merge] DRY RUN - previewing merges without executing:")
            for source, target in merge_pairs:
                print(
                    f"  - Would merge row {source.row_number} ({source.company}) → row {target.row_number} ({target.company})"
                )
            return applications, len(merge_pairs)

        # Execute merges
        merged_count = 0
        rows_to_delete = []
        batch_updates = []

        # Sort by source row descending to avoid row number shifts during deletion
        merge_pairs_sorted = sorted(
            merge_pairs, key=lambda pair: pair[0].row_number, reverse=True
        )

        for source, target in merge_pairs_sorted:
            # Execute merge
            updated_target = self.execute_merge(source, target)

            # Record merge in tracker
            self.tracker.record_merge(
                source_thread_ids=source.get_thread_ids(),
                target_thread_ids=updated_target.thread_id or "",
                source_row=source.row_number,
                target_row=target.row_number,
                source_company=source.company,
                target_company=target.company,
            )

            # Prepare batch update for target row
            cell_range = f"A{target.row_number}:K{target.row_number}"  # K is column 11
            batch_updates.append(
                {"range": cell_range, "values": [updated_target.to_row()]}
            )

            # Mark source row for deletion
            rows_to_delete.append(source.row_number)

            merged_count += 1

        # Execute batch update
        if batch_updates:
            print(f"\n[Merge] Updating {len(batch_updates)} target row(s)...")
            self.client.batch_update(batch_updates)

        # Delete source rows (from highest to lowest to avoid row shifts)
        if rows_to_delete:
            print(f"[Merge] Deleting {len(rows_to_delete)} source row(s)...")
            for row_num in rows_to_delete:
                self._delete_row(row_num)

        print(f"\n[Merge] ✓ Completed {merged_count} merge(s)")

        # Refresh applications list
        updated_apps = self._reload_applications()

        return updated_apps, merged_count

    def _delete_row(self, row_number: int):
        """Delete a row from the spreadsheet.

        Args:
            row_number: Row number to delete (1-indexed)
        """
        # Use gspread's delete_rows method
        if self.client.worksheet:
            self.client.worksheet.delete_rows(row_number)

    def _reload_applications(self) -> List[Application]:
        """Reload all applications from spreadsheet.

        Returns:
            list: Fresh list of Application objects
        """
        rows = self.client.get_all_rows()

        applications = []
        for i, row in enumerate(rows[1:], start=2):  # Skip header
            if row and row[0]:  # Skip empty rows
                try:
                    app = Application.from_row(row, row_number=i)
                    applications.append(app)
                except Exception as e:
                    print(f"Error parsing row {i}: {e}")
                    continue

        return applications
