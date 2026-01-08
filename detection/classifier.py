"""Classify email type and map to application status."""

from typing import Optional

from models.email import Email
from config.keywords import STATUS_KEYWORDS
from utils.text_utils import contains_any_keyword


class EmailClassifier:
    """Classify job email type and determine status."""

    def classify(self, email: Email) -> tuple[Optional[str], Optional[str]]:
        """Classify email and determine status.

        Args:
            email: Email to classify

        Returns:
            tuple: (email_type, status)
        """
        # Combine subject and body for analysis
        text = (email.subject + " " + email.body).lower()

        # Check each status type (order matters - check rejection before others)
        if contains_any_keyword(text, STATUS_KEYWORDS["REJECTED"]):
            return "rejection", "Rejected"

        if contains_any_keyword(text, STATUS_KEYWORDS["OFFER"]):
            return "offer", "Offer Received"

        if contains_any_keyword(text, STATUS_KEYWORDS["INTERVIEW_SCHEDULED"]):
            return "interview", "Interview Scheduled"

        if contains_any_keyword(text, STATUS_KEYWORDS["ASSESSMENT"]):
            return "assessment", "Assessment Sent"

        if contains_any_keyword(text, STATUS_KEYWORDS["APPLICATION_RECEIVED"]):
            return "application_received", "Application Received"

        # Default: if none of the above, assume initial application
        return "application", "Applied"

    def classify_batch(self, emails: list[Email]) -> list[Email]:
        """Classify multiple emails.

        Args:
            emails: List of emails to classify

        Returns:
            list: Emails with classification results set
        """
        for email in emails:
            email_type, status = self.classify(email)
            email.email_type = email_type
            email.status = status

        return emails
