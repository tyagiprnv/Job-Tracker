"""Google Sheets API client wrapper."""

import gspread
import time
from typing import Optional
from functools import wraps

from auth.sheets_auth import get_sheets_client
from config.settings import SPREADSHEET_ID, SHEET_COLUMNS


def retry_on_rate_limit(max_retries=5, base_delay=1.0):
    """Decorator to retry operations with exponential backoff on rate limit errors.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds (will be exponentially increased)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except gspread.exceptions.APIError as e:
                    # Check if it's a rate limit error (429)
                    if "429" in str(e) or "Quota exceeded" in str(e):
                        if retries == max_retries:
                            print(f"\n[Error] Rate limit exceeded after {max_retries} retries")
                            raise

                        # Calculate exponential backoff delay
                        delay = base_delay * (2 ** retries)
                        retries += 1
                        print(f"\n[Warning] Rate limit hit. Waiting {delay:.1f}s before retry {retries}/{max_retries}...")
                        time.sleep(delay)
                    else:
                        # Not a rate limit error, re-raise immediately
                        raise
            return None
        return wrapper
    return decorator


class SheetsClient:
    """Wrapper for Google Sheets API using gspread."""

    def __init__(self, spreadsheet_id: str = SPREADSHEET_ID):
        """Initialize sheets client.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
        """
        self.client = get_sheets_client()
        self.spreadsheet_id = spreadsheet_id
        self.spreadsheet = None
        self.worksheet = None

    def open_spreadsheet(self, sheet_index: int = 0):
        """Open spreadsheet and worksheet.

        Args:
            sheet_index: Index of worksheet to open (default: first sheet)

        Raises:
            gspread.exceptions.SpreadsheetNotFound: If spreadsheet not found
        """
        self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
        self.worksheet = self.spreadsheet.get_worksheet(sheet_index)

        # Initialize headers if sheet is empty
        if self.worksheet.row_count == 0 or not self.worksheet.row_values(1):
            self.worksheet.append_row(SHEET_COLUMNS)

    def get_all_rows(self) -> list[list]:
        """Get all rows from worksheet.

        Returns:
            list: List of rows (each row is a list of cell values)
        """
        if not self.worksheet:
            self.open_spreadsheet()

        return self.worksheet.get_all_values()

    @retry_on_rate_limit(max_retries=5, base_delay=1.0)
    def append_row(self, row: list):
        """Append a new row to worksheet.

        Args:
            row: List of cell values to append
        """
        if not self.worksheet:
            self.open_spreadsheet()

        self.worksheet.append_row(row)

    @retry_on_rate_limit(max_retries=5, base_delay=1.0)
    def append_rows(self, rows: list[list]):
        """Append multiple rows to worksheet in a single batch operation.

        Args:
            rows: List of rows (each row is a list of cell values)
        """
        if not self.worksheet:
            self.open_spreadsheet()

        if not rows:
            return

        # Use append_rows for efficient batch insertion
        self.worksheet.append_rows(rows, value_input_option='USER_ENTERED')

    @retry_on_rate_limit(max_retries=5, base_delay=1.0)
    def update_row(self, row_number: int, row: list):
        """Update an existing row.

        Args:
            row_number: Row number (1-indexed)
            row: List of cell values
        """
        if not self.worksheet:
            self.open_spreadsheet()

        # Update all cells in the row (K is column 11 for Merge Into Row)
        cell_range = f"A{row_number}:K{row_number}"
        self.worksheet.update(cell_range, [row])

    def update_cell(self, row: int, col: int, value: str):
        """Update a single cell.

        Args:
            row: Row number (1-indexed)
            col: Column number (1-indexed)
            value: Cell value
        """
        if not self.worksheet:
            self.open_spreadsheet()

        self.worksheet.update_cell(row, col, value)

    @retry_on_rate_limit(max_retries=5, base_delay=1.0)
    def delete_row(self, row_number: int):
        """Delete a row from the worksheet.

        Args:
            row_number: Row number to delete (1-indexed)
        """
        if not self.worksheet:
            self.open_spreadsheet()

        self.worksheet.delete_rows(row_number)

    def find_row(self, search_col: int, search_value: str) -> Optional[int]:
        """Find row number by searching a column.

        Args:
            search_col: Column number to search (1-indexed)
            search_value: Value to search for

        Returns:
            int: Row number (1-indexed) or None if not found
        """
        if not self.worksheet:
            self.open_spreadsheet()

        try:
            cell = self.worksheet.find(search_value, in_column=search_col)
            return cell.row if cell else None
        except gspread.exceptions.CellNotFound:
            return None

    @retry_on_rate_limit(max_retries=5, base_delay=1.0)
    def batch_update(self, updates: list[dict]):
        """Perform batch updates.

        Args:
            updates: List of update dicts with 'range' and 'values' keys
        """
        if not self.worksheet:
            self.open_spreadsheet()

        self.worksheet.batch_update(updates)
