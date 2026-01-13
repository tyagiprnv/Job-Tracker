"""LLM-based email analyzer."""

import json
from typing import Optional
from pathlib import Path

from models.email import Email
from llm.llm_client import LLMClient
from config.settings import LLM_CACHE_FILE


class LLMEmailAnalyzer:
    """Analyze emails using LLM."""

    def __init__(self):
        """Initialize analyzer."""
        self.client = LLMClient()
        self.cache_file = LLM_CACHE_FILE
        self.cache = self._load_cache()
        self.all_emails = []  # Store all emails for thread context

    def analyze(self, email: Email) -> bool:
        """Analyze email and populate fields.

        Args:
            email: Email object to analyze

        Returns:
            bool: True if successfully analyzed
        """
        # Check cache
        if email.message_id in self.cache:
            self._apply_cached_result(email, self.cache[email.message_id])
            return True

        # Build thread context from previous emails in the same thread
        thread_context = self._build_thread_context(email)

        # Call LLM
        result = self.client.analyze_email(
            subject=email.subject,
            body=email.body,
            sender=email.sender_email,
            thread_context=thread_context,
        )

        if not result:
            # Fallback to rules-based if LLM fails
            print(f"LLM failed for {email.message_id}, using rules fallback")
            return self._fallback_to_rules(email)

        # Cache result
        self.cache[email.message_id] = result
        self._save_cache()

        # Apply to email object
        self._apply_result(email, result)

        return True

    def _apply_result(self, email: Email, result: dict):
        """Apply LLM result to email object.

        Args:
            email: Email object to update
            result: LLM analysis result
        """
        email.is_job_related = result.get("is_job_related", False)
        email.detection_score = int(result.get("confidence", 0) * 100)
        email.company = result.get("company") or "Unknown"
        email.position = result.get("position") or "Unknown Position"
        email.status = result.get("status") or "Applied"
        email.email_type = self._map_status_to_type(email.status)

    def _apply_cached_result(self, email: Email, result: dict):
        """Apply cached result to email.

        Args:
            email: Email object to update
            result: Cached analysis result
        """
        self._apply_result(email, result)

    def _map_status_to_type(self, status: str) -> str:
        """Map status to email type.

        Args:
            status: Application status

        Returns:
            str: Email type
        """
        status_lower = status.lower()
        if "reject" in status_lower:
            return "rejection"
        elif "interview" in status_lower:
            return "interview"
        elif "offer" in status_lower:
            return "offer"
        elif "assessment" in status_lower:
            return "assessment"
        elif "received" in status_lower:
            return "application_received"
        else:
            return "application"

    def _build_thread_context(self, email: Email) -> str:
        """Build context from previous emails in the same thread.

        Args:
            email: Current email being analyzed

        Returns:
            str: Thread context string (empty if no thread emails found)
        """
        if not email.thread_id:
            return ""

        # Find other emails in the same thread
        thread_emails = []
        for other_email in self.all_emails:
            if (
                other_email.thread_id == email.thread_id
                and other_email.message_id != email.message_id
                and other_email.date < email.date  # Only previous emails
            ):
                thread_emails.append(other_email)

        # Also check cache for thread emails with extracted info
        thread_info = []
        for other_email in thread_emails:
            if other_email.message_id in self.cache:
                cached = self.cache[other_email.message_id]
                if cached.get("is_job_related") and cached.get("company"):
                    thread_info.append(
                        f"  - Earlier email: Company={cached.get('company')}, "
                        f"Position={cached.get('position')}, "
                        f"Status={cached.get('status')}"
                    )

        if not thread_info:
            return ""

        return (
            "THREAD CONTEXT (previous emails in this conversation):\n"
            + "\n".join(thread_info)
            + "\n\nUse this context to extract company/position if not mentioned in current email.\n"
        )

    def _fallback_to_rules(self, email: Email) -> bool:
        """Fallback to original rules-based detection.

        Args:
            email: Email object to analyze

        Returns:
            bool: True if successfully analyzed
        """
        try:
            from detection.detector import JobEmailDetector
            from detection.extractor import InfoExtractor
            from detection.classifier import EmailClassifier

            detector = JobEmailDetector()
            is_job, score = detector.detect(email)

            if not is_job:
                email.is_job_related = False
                return True

            email.is_job_related = True
            email.detection_score = score

            extractor = InfoExtractor()
            email.company, email.position = extractor.extract_all(email)

            classifier = EmailClassifier()
            email.email_type, email.status = classifier.classify(email)

            return True
        except Exception as e:
            print(f"Fallback failed: {e}")
            return False

    def analyze_batch(self, emails: list[Email]) -> list[Email]:
        """Analyze multiple emails.

        Args:
            emails: List of emails to analyze

        Returns:
            list: Job-related emails only
        """
        # Store all emails for thread context building
        self.all_emails = emails

        job_emails = []

        for i, email in enumerate(emails):
            if (i + 1) % 10 == 0:
                print(f"Analyzing: {i + 1}/{len(emails)}")

            success = self.analyze(email)

            if success and email.is_job_related:
                job_emails.append(email)

        return job_emails

    def _load_cache(self) -> dict:
        """Load cache from disk.

        Returns:
            dict: Cache dictionary (message_id -> result)
        """
        if not self.cache_file.exists():
            return {}

        try:
            with open(self.cache_file, "r") as f:
                cache = json.load(f)
                print(f"Loaded {len(cache)} cached results from {self.cache_file.name}")
                return cache
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load cache file: {e}")
            print("Starting with empty cache")
            return {}

    def _save_cache(self):
        """Save cache to disk."""
        try:
            with open(self.cache_file, "w") as f:
                json.dump(self.cache, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save cache file: {e}")
