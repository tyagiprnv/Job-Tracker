"""Track false positive detections to improve accuracy."""

import json
from typing import Optional, Set
from pathlib import Path

from config.settings import FALSE_POSITIVES_FILE


class FalsePositivesTracker:
    """Track emails/applications marked as false positives by user deletion."""

    def __init__(self):
        """Initialize tracker."""
        self.file_path = FALSE_POSITIVES_FILE
        self.false_positives = self._load()

    def _load(self) -> dict:
        """Load false positives from disk.

        Returns:
            dict: False positives data structure
        """
        if not self.file_path.exists():
            return {"message_ids": [], "companies": {}}

        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
                print(
                    f"Loaded {len(data.get('message_ids', []))} false positive message IDs"
                )
                return data
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load false positives file: {e}")
            return {"message_ids": [], "companies": {}}

    def _save(self):
        """Save false positives to disk."""
        try:
            with open(self.file_path, "w") as f:
                json.dump(self.false_positives, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save false positives file: {e}")

    def is_false_positive(
        self, message_id: str, company: str, position: str
    ) -> bool:
        """Check if email/application is a known false positive.

        Args:
            message_id: Gmail message ID
            company: Company name
            position: Position title

        Returns:
            bool: True if this is a known false positive
        """
        # Check message ID (most reliable)
        if message_id in self.false_positives.get("message_ids", []):
            return True

        # Check company+position combination
        companies = self.false_positives.get("companies", {})
        company_lower = company.lower()

        if company_lower in companies:
            positions = companies[company_lower]
            if position.lower() in positions:
                return True

        return False

    def add_false_positive(
        self, message_id: str, company: str, position: str
    ):
        """Mark email/application as false positive.

        Args:
            message_id: Gmail message ID
            company: Company name
            position: Position title
        """
        # Add message ID
        if "message_ids" not in self.false_positives:
            self.false_positives["message_ids"] = []

        if message_id not in self.false_positives["message_ids"]:
            self.false_positives["message_ids"].append(message_id)

        # Add company+position combination
        if "companies" not in self.false_positives:
            self.false_positives["companies"] = {}

        company_lower = company.lower()
        position_lower = position.lower()

        if company_lower not in self.false_positives["companies"]:
            self.false_positives["companies"][company_lower] = []

        if (
            position_lower
            not in self.false_positives["companies"][company_lower]
        ):
            self.false_positives["companies"][company_lower].append(
                position_lower
            )

        self._save()
        print(
            f"Recorded false positive: {company} - {position} (message: {message_id[:8]}...)"
        )

    def get_stats(self) -> dict:
        """Get false positives statistics.

        Returns:
            dict: Statistics about tracked false positives
        """
        return {
            "message_ids_count": len(
                self.false_positives.get("message_ids", [])
            ),
            "company_position_combinations": sum(
                len(positions)
                for positions in self.false_positives.get(
                    "companies", {}
                ).values()
            ),
        }
