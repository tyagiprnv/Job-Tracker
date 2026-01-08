"""Gmail API client wrapper."""

import time
from typing import Optional
from googleapiclient.errors import HttpError

from auth.gmail_auth import get_gmail_service


class GmailClient:
    """Wrapper for Gmail API with error handling and retry logic."""

    def __init__(self):
        """Initialize Gmail client."""
        self.service = get_gmail_service()

    def list_messages(
        self, query: str = "", max_results: int = 100, page_token: Optional[str] = None
    ) -> dict:
        """List messages matching query.

        Args:
            query: Gmail search query
            max_results: Maximum number of results
            page_token: Page token for pagination

        Returns:
            dict: Response containing messages and nextPageToken

        Raises:
            HttpError: If API request fails
        """
        try:
            response = (
                self.service.users()
                .messages()
                .list(
                    userId="me",
                    q=query,
                    maxResults=max_results,
                    pageToken=page_token,
                )
                .execute()
            )
            return response
        except HttpError as e:
            if e.resp.status == 429:  # Rate limit
                print("Rate limit hit, waiting 10 seconds...")
                time.sleep(10)
                return self.list_messages(query, max_results, page_token)
            raise

    def get_message(self, message_id: str, format: str = "full") -> dict:
        """Get message by ID.

        Args:
            message_id: Gmail message ID
            format: Message format (full, metadata, minimal, raw)

        Returns:
            dict: Message data

        Raises:
            HttpError: If API request fails
        """
        try:
            message = (
                self.service.users()
                .messages()
                .get(userId="me", id=message_id, format=format)
                .execute()
            )
            return message
        except HttpError as e:
            if e.resp.status == 429:  # Rate limit
                print("Rate limit hit, waiting 10 seconds...")
                time.sleep(10)
                return self.get_message(message_id, format)
            raise

    def get_thread(self, thread_id: str) -> dict:
        """Get email thread by ID.

        Args:
            thread_id: Gmail thread ID

        Returns:
            dict: Thread data containing all messages

        Raises:
            HttpError: If API request fails
        """
        try:
            thread = (
                self.service.users()
                .threads()
                .get(userId="me", id=thread_id)
                .execute()
            )
            return thread
        except HttpError as e:
            if e.resp.status == 429:  # Rate limit
                print("Rate limit hit, waiting 10 seconds...")
                time.sleep(10)
                return self.get_thread(thread_id)
            raise

    def get_all_messages(self, query: str = "", max_results: int = 500) -> list:
        """Get all messages matching query (handles pagination).

        Args:
            query: Gmail search query
            max_results: Maximum total results

        Returns:
            list: List of message metadata dicts

        Raises:
            HttpError: If API request fails
        """
        messages = []
        page_token = None
        total_fetched = 0

        while total_fetched < max_results:
            # Fetch next page
            batch_size = min(100, max_results - total_fetched)
            response = self.list_messages(query, batch_size, page_token)

            # Add messages from this page
            if "messages" in response:
                messages.extend(response["messages"])
                total_fetched += len(response["messages"])

            # Check for more pages
            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return messages
