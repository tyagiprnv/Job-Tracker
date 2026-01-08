"""Google Sheets API client wrapper."""

import gspread
from typing import Optional

from auth.sheets_auth import get_sheets_client
from config.settings import SPREADSHEET_ID, SHEET_COLUMNS


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

    def append_row(self, row: list):
        """Append a new row to worksheet.

        Args:
            row: List of cell values to append
        """
        if not self.worksheet:
            self.open_spreadsheet()

        self.worksheet.append_row(row)

    def update_row(self, row_number: int, row: list):
        """Update an existing row.

        Args:
            row_number: Row number (1-indexed)
            row: List of cell values
        """
        if not self.worksheet:
            self.open_spreadsheet()

        # Update all cells in the row
        cell_range = f"A{row_number}:I{row_number}"
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

    def batch_update(self, updates: list[dict]):
        """Perform batch updates.

        Args:
            updates: List of update dicts with 'range' and 'values' keys
        """
        if not self.worksheet:
            self.open_spreadsheet()

        self.worksheet.batch_update(updates)
