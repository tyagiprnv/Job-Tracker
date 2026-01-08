"""Email data model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Email:
    """Represents a parsed email from Gmail."""

    message_id: str
    thread_id: str
    sender: str
    sender_email: str
    subject: str
    body: str
    date: datetime
    gmail_link: str

    # Extracted/classified information
    is_job_related: bool = False
    detection_score: int = 0
    company: Optional[str] = None
    position: Optional[str] = None
    status: Optional[str] = None
    email_type: Optional[str] = None

    def __str__(self) -> str:
        """String representation of email."""
        return f"Email from {self.sender} ({self.date.strftime('%Y-%m-%d')}): {self.subject}"

    def to_dict(self) -> dict:
        """Convert email to dictionary."""
        return {
            "message_id": self.message_id,
            "thread_id": self.thread_id,
            "sender": self.sender,
            "sender_email": self.sender_email,
            "subject": self.subject,
            "body": self.body[:500],  # Truncate for readability
            "date": self.date.isoformat(),
            "gmail_link": self.gmail_link,
            "is_job_related": self.is_job_related,
            "detection_score": self.detection_score,
            "company": self.company,
            "position": self.position,
            "status": self.status,
            "email_type": self.email_type,
        }
