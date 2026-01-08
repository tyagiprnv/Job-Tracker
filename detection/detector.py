"""Job email detection with scoring algorithm."""

from models.email import Email
from config.keywords import (
    ATS_DOMAINS,
    RECRUITING_REGEX,
    DETECTION_KEYWORDS,
    EXCLUSION_PATTERNS,
    JOB_BOARD_DOMAINS,
)
from config.settings import DETECTION_THRESHOLD
from utils.text_utils import extract_email_domain, contains_any_keyword


class JobEmailDetector:
    """Detect if an email is job-related using scoring algorithm."""

    def detect(self, email: Email) -> tuple[bool, int]:
        """Detect if email is job-related.

        Args:
            email: Email object to analyze

        Returns:
            tuple: (is_job_related, detection_score)
        """
        score = 0

        # Check exclusion patterns first
        if self._is_excluded(email):
            return False, 0

        # 1. Check sender domain (5 points for ATS platforms)
        domain = extract_email_domain(email.sender_email)
        if any(ats_domain in domain for ats_domain in ATS_DOMAINS):
            score += 5

        # Check if from job board (likely newsletter, exclude)
        if any(job_board in domain for job_board in JOB_BOARD_DOMAINS):
            # Could be newsletter, reduce score
            score -= 3

        # 2. Check recruiting email patterns (3 points)
        if RECRUITING_REGEX.search(email.sender_email):
            score += 3

        # 3. Check subject keywords (3 points for high confidence)
        subject_lower = email.subject.lower()
        if contains_any_keyword(subject_lower, DETECTION_KEYWORDS["HIGH_CONFIDENCE"]):
            score += 3
        elif contains_any_keyword(
            subject_lower, DETECTION_KEYWORDS["MEDIUM_CONFIDENCE"]
        ):
            score += 2

        # 4. Check body keywords (weighted)
        body_lower = email.body.lower()

        if contains_any_keyword(body_lower, DETECTION_KEYWORDS["HIGH_CONFIDENCE"]):
            score += 3
        elif contains_any_keyword(
            body_lower, DETECTION_KEYWORDS["MEDIUM_CONFIDENCE"]
        ):
            score += 2
        elif contains_any_keyword(body_lower, DETECTION_KEYWORDS["LOW_CONFIDENCE"]):
            score += 1

        # Determine if job-related
        is_job_related = score >= DETECTION_THRESHOLD

        return is_job_related, score

    def _is_excluded(self, email: Email) -> bool:
        """Check if email matches exclusion patterns.

        Args:
            email: Email to check

        Returns:
            bool: True if email should be excluded
        """
        # Check subject and body for exclusion patterns
        text = (email.subject + " " + email.body).lower()

        return contains_any_keyword(text, EXCLUSION_PATTERNS)

    def detect_batch(self, emails: list[Email]) -> list[Email]:
        """Detect job emails in batch.

        Args:
            emails: List of emails to analyze

        Returns:
            list: List of emails with detection results set
        """
        job_emails = []

        for email in emails:
            is_job_related, score = self.detect(email)
            email.is_job_related = is_job_related
            email.detection_score = score

            if is_job_related:
                job_emails.append(email)

        return job_emails
