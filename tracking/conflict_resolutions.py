"""Track conflict resolution decisions to enable auto-resolution."""

import json
from typing import Optional
from config.settings import CONFLICT_RESOLUTIONS_FILE
from utils.text_utils import normalize_text


class ConflictResolutionTracker:
    """Track user decisions for conflict resolution."""

    def __init__(self):
        """Initialize tracker."""
        self.file_path = CONFLICT_RESOLUTIONS_FILE
        self.data = self._load()

    def _load(self) -> dict:
        """Load resolutions from disk.

        Returns:
            dict: Resolutions data structure
        """
        if not self.file_path.exists():
            return {"resolutions": {}}

        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
                count = len(data.get("resolutions", {}))
                if count > 0:
                    print(f"Loaded {count} conflict resolution(s)")
                return data
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load conflict resolutions file: {e}")
            return {"resolutions": {}}

    def _save(self):
        """Save resolutions to disk."""
        try:
            with open(self.file_path, "w") as f:
                json.dump(self.data, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save conflict resolutions file: {e}")

    def _make_key(
        self, field_name: str, spreadsheet_value: str, email_value: str
    ) -> str:
        """Generate normalized lookup key.

        Args:
            field_name: "Company" or "Position"
            spreadsheet_value: Value from spreadsheet
            email_value: Value from email

        Returns:
            str: Normalized key in format "{field}:{norm_ss}:{norm_email}"
        """
        norm_ss = normalize_text(spreadsheet_value)
        norm_email = normalize_text(email_value)
        return f"{field_name.lower()}:{norm_ss}:{norm_email}"

    def find_resolution(
        self, field_name: str, spreadsheet_value: str, email_value: str
    ) -> Optional[dict]:
        """Find existing resolution for conflict pattern.

        Args:
            field_name: "Company" or "Position"
            spreadsheet_value: Value from spreadsheet
            email_value: Value from email

        Returns:
            dict: Resolution dict with keys: field_name, spreadsheet_value,
                  email_value, chosen_value, resolution_type
            None: If no resolution found
        """
        key = self._make_key(field_name, spreadsheet_value, email_value)
        return self.data["resolutions"].get(key)

    def save_resolution(
        self,
        field_name: str,
        spreadsheet_value: str,
        email_value: str,
        chosen_value: str,
        resolution_type: str,
    ):
        """Save a new conflict resolution.

        Args:
            field_name: "Company" or "Position"
            spreadsheet_value: Value from spreadsheet
            email_value: Value from email
            chosen_value: Value user chose to use
            resolution_type: "keep_spreadsheet", "use_email", or "manual"
        """
        key = self._make_key(field_name, spreadsheet_value, email_value)

        self.data["resolutions"][key] = {
            "field_name": field_name,
            "spreadsheet_value": spreadsheet_value,
            "email_value": email_value,
            "chosen_value": chosen_value,
            "resolution_type": resolution_type,
        }

        self._save()
        print(
            f"Saved resolution: {field_name} '{spreadsheet_value}' vs '{email_value}' → '{chosen_value}'"
        )
