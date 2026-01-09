"""Track processed emails to prevent double-counting."""

import json
from typing import Set
from config.settings import PROCESSED_EMAILS_FILE


class ProcessedEmailsTracker:
    """Track which emails have already been processed."""

    def __init__(self):
        """Initialize tracker."""
        self.file_path = PROCESSED_EMAILS_FILE
        self.processed_ids: Set[str] = self._load()

    def _load(self) -> Set[str]:
        """Load processed message IDs from disk.

        Returns:
            set: Set of processed message IDs
        """
        if not self.file_path.exists():
            return set()

        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
                ids = set(data.get("message_ids", []))
                print(f"Loaded {len(ids)} processed email IDs")
                return ids
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load processed emails file: {e}")
            return set()

    def _save(self):
        """Save processed message IDs to disk."""
        try:
            with open(self.file_path, "w") as f:
                json.dump({"message_ids": list(self.processed_ids)}, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save processed emails file: {e}")

    def is_processed(self, message_id: str) -> bool:
        """Check if email has already been processed.

        Args:
            message_id: Gmail message ID

        Returns:
            bool: True if already processed
        """
        return message_id in self.processed_ids

    def mark_processed(self, message_id: str):
        """Mark email as processed.

        Args:
            message_id: Gmail message ID
        """
        if message_id not in self.processed_ids:
            self.processed_ids.add(message_id)
            self._save()

    def get_stats(self) -> dict:
        """Get statistics about processed emails.

        Returns:
            dict: Statistics
        """
        return {"total_processed": len(self.processed_ids)}
