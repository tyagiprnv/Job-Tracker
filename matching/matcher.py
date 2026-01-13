"""Match emails to existing applications."""

from datetime import datetime, timedelta
from typing import Optional
from rapidfuzz import fuzz

from models.email import Email
from models.application import Application
from utils.text_utils import normalize_company_name
from config.settings import MATCHING_THRESHOLD
from tracking.merged_applications import MergedApplicationsTracker


class ApplicationMatcher:
    """Match emails to existing applications using multiple strategies."""

    def __init__(self):
        """Initialize matcher with merge tracking."""
        self.merged_tracker = MergedApplicationsTracker()

    def find_match(
        self, email: Email, applications: list[Application]
    ) -> tuple[Optional[Application], int]:
        """Find matching application for email.

        Args:
            email: Email to match
            applications: List of existing applications

        Returns:
            tuple: (matched_application, confidence_score)
        """
        if not applications:
            return None, 0

        # Strategy 1: Thread ID match (exact match, 100% confidence)
        match, confidence = self._match_by_thread_id(email, applications)
        if match:
            return match, confidence

        # Strategy 2: Exact company + position match (95% confidence)
        match, confidence = self._match_exact(email, applications)
        if match:
            return match, confidence

        # Strategy 3: Fuzzy matching (80-90% confidence)
        match, confidence = self._match_fuzzy(email, applications)
        if match:
            return match, confidence

        # Strategy 4: Recent company-only match (70% confidence)
        match, confidence = self._match_recent_company(email, applications)
        if match:
            return match, confidence

        # No match found
        return None, 0

    def _match_by_thread_id(
        self, email: Email, applications: list[Application]
    ) -> tuple[Optional[Application], int]:
        """Match by Gmail thread ID (supports merged thread IDs).

        Args:
            email: Email to match
            applications: List of applications

        Returns:
            tuple: (matched_application, confidence)
        """
        email_thread_id = email.thread_id

        # Check if email's thread ID was merged into another application
        merged_target = self.merged_tracker.get_merged_thread_ids(email_thread_id)
        if merged_target:
            # Email's thread was merged - search for target thread IDs
            target_thread_ids = [tid.strip() for tid in merged_target.split(",")]
            for app in applications:
                app_thread_ids = app.get_thread_ids()
                if any(tid in app_thread_ids for tid in target_thread_ids):
                    return app, 100

        # Normal thread ID matching (supports CSV)
        for app in applications:
            app_thread_ids = app.get_thread_ids()
            if email_thread_id in app_thread_ids:
                return app, 100

        return None, 0

    def _match_exact(
        self, email: Email, applications: list[Application]
    ) -> tuple[Optional[Application], int]:
        """Match by exact company and position.

        Args:
            email: Email to match
            applications: List of applications

        Returns:
            tuple: (matched_application, confidence)
        """
        # Skip exact match if company or position is missing/unknown
        # Let fuzzy/recent company handle these cases
        if not email.company or not email.position or email.position == "Unknown Position":
            return None, 0

        email_company = normalize_company_name(email.company)
        email_position = email.position.lower().strip()

        for app in applications:
            # Skip apps with unknown position
            if not app.position or app.position == "Unknown Position":
                continue

            app_company = normalize_company_name(app.company)
            app_position = app.position.lower().strip()

            if email_company == app_company and email_position == app_position:
                return app, 95

        return None, 0

    def _match_fuzzy(
        self, email: Email, applications: list[Application]
    ) -> tuple[Optional[Application], int]:
        """Match using fuzzy string matching.

        Args:
            email: Email to match
            applications: List of applications

        Returns:
            tuple: (matched_application, confidence)
        """
        if not email.company:
            return None, 0

        # Check if either side has unknown position
        email_has_unknown = not email.position or email.position == "Unknown Position"

        email_company = normalize_company_name(email.company)
        email_position = email.position.lower().strip() if email.position else ""

        best_match = None
        best_score = 0

        for app in applications:
            app_has_unknown = not app.position or app.position == "Unknown Position"

            app_company = normalize_company_name(app.company)
            app_position = app.position.lower().strip() if app.position else ""

            # Calculate company similarity
            company_score = fuzz.ratio(email_company, app_company)

            # If either has unknown position, use company-only matching
            if email_has_unknown or app_has_unknown:
                # High company similarity required for position-less match
                if company_score >= 90 and company_score > best_score:
                    best_score = company_score
                    best_match = app
            else:
                # Both have positions - use normal fuzzy logic
                position_score = fuzz.ratio(email_position, app_position)

                # Combined score (weighted average)
                combined_score = (company_score * 0.6) + (position_score * 0.4)

                # Require both to be above threshold
                if (
                    company_score >= 85
                    and position_score >= 75
                    and combined_score > best_score
                ):
                    best_score = combined_score
                    best_match = app

        # Return match if above threshold
        if best_match and best_score >= MATCHING_THRESHOLD:
            return best_match, int(best_score)

        return None, 0

    def _match_recent_company(
        self, email: Email, applications: list[Application]
    ) -> tuple[Optional[Application], int]:
        """Match by company name only if it's recent (within 30 days).

        If both email and application have position data, requires position
        similarity >= 75% to prevent matching different roles at same company.

        Args:
            email: Email to match
            applications: List of applications

        Returns:
            tuple: (matched_application, confidence)
        """
        if not email.company:
            return None, 0

        email_company = normalize_company_name(email.company)
        recent_threshold = datetime.now() - timedelta(days=30)

        # Find all recent applications to this company
        recent_matches = []
        for app in applications:
            app_company = normalize_company_name(app.company)
            if app_company == email_company and app.application_date >= recent_threshold:
                recent_matches.append(app)

        # If exactly one recent match found
        if len(recent_matches) == 1:
            app = recent_matches[0]

            # Check if both have real position data (not "Unknown Position")
            email_has_real_position = (
                email.position
                and email.position.strip()
                and email.position != "Unknown Position"
            )
            app_has_real_position = (
                app.position
                and app.position.strip()
                and app.position != "Unknown Position"
            )

            # If both have real position data, require similarity
            if email_has_real_position and app_has_real_position:
                position_score = fuzz.ratio(
                    email.position.lower().strip(),
                    app.position.lower().strip()
                )
                # Only match if positions are similar (85% threshold)
                # Higher threshold prevents matching different levels/roles
                # (e.g., "Software Engineer" vs "Senior Software Engineer")
                if position_score >= 85:
                    return app, 70
                else:
                    # Positions too different - don't match
                    return None, 0

            # If position missing/unknown from either, fall back to company-only match
            # (handles generic emails like "Thanks for applying")
            return app, 70

        # If multiple matches, can't determine which one
        return None, 0
