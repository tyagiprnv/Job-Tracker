"""Match emails to existing applications."""

from datetime import datetime, timedelta
from typing import Optional
from rapidfuzz import fuzz

from models.email import Email
from models.application import Application
from utils.text_utils import normalize_company_name
from config.settings import MATCHING_THRESHOLD


class ApplicationMatcher:
    """Match emails to existing applications using multiple strategies."""

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
        """Match by Gmail thread ID.

        Args:
            email: Email to match
            applications: List of applications

        Returns:
            tuple: (matched_application, confidence)
        """
        for app in applications:
            if app.thread_id and app.thread_id == email.thread_id:
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
        if not email.company or not email.position:
            return None, 0

        email_company = normalize_company_name(email.company)
        email_position = email.position.lower().strip()

        for app in applications:
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
        if not email.company or not email.position:
            return None, 0

        email_company = normalize_company_name(email.company)
        email_position = email.position.lower().strip()

        best_match = None
        best_score = 0

        for app in applications:
            app_company = normalize_company_name(app.company)
            app_position = app.position.lower().strip()

            # Calculate similarity scores
            company_score = fuzz.ratio(email_company, app_company)
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

            # If both have position data, require similarity
            if email.position and email.position.strip() and app.position and app.position.strip():
                position_score = fuzz.ratio(
                    email.position.lower().strip(),
                    app.position.lower().strip()
                )
                # Only match if positions are similar (75% threshold)
                if position_score >= 75:
                    return app, 70
                else:
                    # Positions too different - don't match
                    return None, 0

            # If position missing from either, fall back to company-only match
            # (handles generic emails like "Thanks for applying")
            return app, 70

        # If multiple matches, can't determine which one
        return None, 0
