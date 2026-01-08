"""Fetch emails from Gmail."""

from datetime import datetime, timedelta
from typing import List

from gmail.client import GmailClient
from config.settings import GMAIL_SEARCH_DAYS, GMAIL_MAX_RESULTS


class EmailFetcher:
    """Fetch emails from Gmail with filtering."""

    def __init__(self):
        """Initialize email fetcher."""
        self.client = GmailClient()

    def build_search_query(self, days_back: int = GMAIL_SEARCH_DAYS) -> str:
        """Build Gmail search query.

        Args:
            days_back: Number of days to search back

        Returns:
            str: Gmail search query
        """
        # Calculate date threshold
        date_threshold = datetime.now() - timedelta(days=days_back)
        date_str = date_threshold.strftime("%Y/%m/%d")

        # Build query
        # Search for emails after date, exclude sent emails
        query = f"after:{date_str} -from:me"

        return query

    def fetch_recent_emails(
        self, days_back: int = GMAIL_SEARCH_DAYS, max_results: int = GMAIL_MAX_RESULTS
    ) -> List[dict]:
        """Fetch recent emails.

        Args:
            days_back: Number of days to search back
            max_results: Maximum number of emails to fetch

        Returns:
            list: List of email message IDs and thread IDs
        """
        query = self.build_search_query(days_back)
        print(f"Searching Gmail with query: {query}")
        print(f"Maximum results: {max_results}")

        messages = self.client.get_all_messages(query, max_results)
        print(f"Found {len(messages)} emails")

        return messages

    def fetch_message_details(self, message_id: str) -> dict:
        """Fetch full message details.

        Args:
            message_id: Gmail message ID

        Returns:
            dict: Full message data
        """
        return self.client.get_message(message_id, format="full")

    def fetch_messages_batch(self, message_ids: List[str]) -> List[dict]:
        """Fetch multiple messages.

        Args:
            message_ids: List of message IDs

        Returns:
            list: List of full message data
        """
        messages = []
        total = len(message_ids)

        for i, msg_id in enumerate(message_ids, 1):
            if i % 10 == 0:
                print(f"Fetching messages: {i}/{total}")

            message = self.fetch_message_details(msg_id)
            messages.append(message)

        return messages
