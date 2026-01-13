"""Track merged applications to enable thread ID lookup."""

import json
from datetime import datetime
from typing import Optional
from config.settings import MERGED_APPLICATIONS_FILE


class MergedApplicationsTracker:
    """Track which applications have been merged and their thread ID mappings."""

    def __init__(self):
        """Initialize tracker."""
        self.file_path = MERGED_APPLICATIONS_FILE
        self.data = self._load()

    def _load(self) -> dict:
        """Load merged applications from disk.

        Returns:
            dict: Merged applications data structure
        """
        if not self.file_path.exists():
            return {"merged_thread_ids": {}, "merge_history": []}

        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
                print(
                    f"Loaded {len(data.get('merged_thread_ids', {}))} merged thread ID mappings"
                )
                return data
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load merged applications file: {e}")
            return {"merged_thread_ids": {}, "merge_history": []}

    def _save(self):
        """Save merged applications to disk."""
        try:
            with open(self.file_path, "w") as f:
                json.dump(self.data, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save merged applications file: {e}")

    def record_merge(
        self,
        source_thread_ids: list[str],
        target_thread_ids: str,
        source_row: int,
        target_row: int,
        source_company: str,
        target_company: str,
    ):
        """Record a merge operation.

        Args:
            source_thread_ids: List of source thread IDs
            target_thread_ids: CSV string of target thread IDs
            source_row: Source row number
            target_row: Target row number
            source_company: Source company name
            target_company: Target company name
        """
        # Map each source thread ID to target thread IDs
        for thread_id in source_thread_ids:
            if thread_id:
                self.data["merged_thread_ids"][thread_id] = target_thread_ids

        # Record in history
        self.data["merge_history"].append(
            {
                "timestamp": datetime.now().isoformat(),
                "source_row": source_row,
                "target_row": target_row,
                "source_company": source_company,
                "target_company": target_company,
            }
        )

        self._save()

    def get_merged_thread_ids(self, thread_id: str) -> Optional[str]:
        """Get target thread IDs for a merged thread ID.

        Args:
            thread_id: Original thread ID

        Returns:
            str: CSV of target thread IDs, or None if not merged
        """
        return self.data.get("merged_thread_ids", {}).get(thread_id)

    def get_stats(self) -> dict:
        """Get statistics about merges.

        Returns:
            dict: Statistics
        """
        return {
            "merged_thread_ids": len(self.data.get("merged_thread_ids", {})),
            "total_merges": len(self.data.get("merge_history", [])),
        }
