"""Parse Gmail messages."""

import base64
from datetime import datetime
from email.utils import parsedate_to_datetime
from bs4 import BeautifulSoup
from typing import Optional

from models.email import Email
from utils.text_utils import (
    extract_sender_name,
    extract_email_address,
    clean_html_text,
)


class EmailParser:
    """Parse Gmail API messages into Email objects."""

    def parse_message(self, message: dict) -> Email:
        """Parse Gmail API message into Email object.

        Args:
            message: Gmail API message dict

        Returns:
            Email: Parsed email object
        """
        # Extract basic fields
        message_id = message["id"]
        thread_id = message["threadId"]

        # Parse headers
        headers = {h["name"]: h["value"] for h in message["payload"]["headers"]}

        sender_field = headers.get("From", "")
        sender = extract_sender_name(sender_field)
        sender_email = extract_email_address(sender_field)
        subject = headers.get("Subject", "")
        date_str = headers.get("Date", "")

        # Parse date
        try:
            date = parsedate_to_datetime(date_str)
            # Convert to timezone-naive datetime for consistency
            if date.tzinfo is not None:
                date = date.replace(tzinfo=None)
        except Exception:
            date = datetime.now()

        # Extract body
        body = self._extract_body(message["payload"])

        # Create Gmail link
        gmail_link = f"https://mail.google.com/mail/u/2/#inbox/{message_id}"

        return Email(
            message_id=message_id,
            thread_id=thread_id,
            sender=sender,
            sender_email=sender_email,
            subject=subject,
            body=body,
            date=date,
            gmail_link=gmail_link,
        )

    def _extract_body(self, payload: dict) -> str:
        """Extract email body from payload.

        Args:
            payload: Message payload from Gmail API

        Returns:
            str: Email body text
        """
        body = ""

        # Check if payload has parts (multipart email)
        if "parts" in payload:
            for part in payload["parts"]:
                # Recursively extract from parts
                body += self._extract_body(part)
        else:
            # Single part email
            mime_type = payload.get("mimeType", "")
            if "data" in payload.get("body", {}):
                data = payload["body"]["data"]
                decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

                # Convert HTML to text if needed
                if "html" in mime_type:
                    body = self._html_to_text(decoded)
                else:
                    body = decoded

        return body

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text.

        Args:
            html: HTML string

        Returns:
            str: Plain text
        """
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Remove script and style elements
            for element in soup(["script", "style", "head", "meta"]):
                element.decompose()

            # Get text
            text = soup.get_text(separator=" ")

            # Clean up
            text = clean_html_text(text)

            return text
        except Exception as e:
            # Fallback: return HTML with tags stripped
            soup = BeautifulSoup(html, "html.parser")
            return soup.get_text()

    def parse_messages(self, messages: list[dict]) -> list[Email]:
        """Parse multiple messages.

        Args:
            messages: List of Gmail API messages

        Returns:
            list: List of Email objects
        """
        emails = []

        for message in messages:
            try:
                email = self.parse_message(message)
                emails.append(email)
            except Exception as e:
                print(f"Error parsing message {message.get('id', 'unknown')}: {e}")
                continue

        return emails
