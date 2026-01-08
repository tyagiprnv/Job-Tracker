"""Extract company and position information from emails."""

import re
from typing import Optional

from models.email import Email
from config.keywords import POSITION_INDICATORS
from utils.text_utils import extract_email_domain, extract_domain_company_name


class InfoExtractor:
    """Extract company and position information from emails."""

    def extract_company(self, email: Email) -> Optional[str]:
        """Extract company name from email.

        Args:
            email: Email object

        Returns:
            str: Company name or None
        """
        company = None

        # Strategy 1: Extract from subject
        company = self._extract_from_subject(email.subject)
        if company:
            return company

        # Strategy 2: Extract from sender domain
        domain = extract_email_domain(email.sender_email)
        company = extract_domain_company_name(domain)
        if company and len(company) > 2:  # Avoid single letters
            return company.title()

        # Strategy 3: Extract from sender name
        if email.sender and not "@" in email.sender:
            # Sender name might be "Company Recruiting"
            parts = email.sender.split()
            if len(parts) > 0:
                # Take first part as potential company name
                potential_company = parts[0]
                if len(potential_company) > 2:
                    return potential_company

        # Strategy 4: Look for patterns in body
        company = self._extract_from_body(email.body)
        if company:
            return company

        return "Unknown"

    def extract_position(self, email: Email) -> Optional[str]:
        """Extract position title from email.

        Args:
            email: Email object

        Returns:
            str: Position title or None
        """
        position = None

        # Strategy 1: Extract from subject
        position = self._extract_position_from_subject(email.subject)
        if position:
            return position

        # Strategy 2: Extract from body using indicators
        position = self._extract_position_from_body(email.body)
        if position:
            return position

        return "Unknown Position"

    def _extract_from_subject(self, subject: str) -> Optional[str]:
        """Extract company from subject line.

        Args:
            subject: Email subject

        Returns:
            str: Company name or None
        """
        # Pattern: "Application at CompanyName"
        match = re.search(r"(?:at|@)\s+([A-Z][A-Za-z0-9\s&]+)", subject)
        if match:
            company = match.group(1).strip()
            # Take first 3 words max
            words = company.split()[:3]
            return " ".join(words)

        # Pattern: "CompanyName - Job Application"
        match = re.search(r"^([A-Z][A-Za-z0-9\s&]+?)\s*[-:]", subject)
        if match:
            company = match.group(1).strip()
            words = company.split()[:3]
            return " ".join(words)

        return None

    def _extract_from_body(self, body: str) -> Optional[str]:
        """Extract company from email body.

        Args:
            body: Email body text

        Returns:
            str: Company name or None
        """
        # Look for patterns like "join our team at CompanyName"
        patterns = [
            r"(?:join|at|with)\s+(?:our\s+team\s+at\s+)?([A-Z][A-Za-z0-9\s&]{2,30})",
            r"team\s+at\s+([A-Z][A-Za-z0-9\s&]{2,30})",
        ]

        for pattern in patterns:
            match = re.search(pattern, body[:500])  # Check first 500 chars
            if match:
                company = match.group(1).strip()
                # Take first 2-3 words
                words = company.split()[:3]
                return " ".join(words)

        return None

    def _extract_position_from_subject(self, subject: str) -> Optional[str]:
        """Extract position from subject.

        Args:
            subject: Email subject

        Returns:
            str: Position title or None
        """
        # Pattern: "Application for Position Title"
        match = re.search(
            r"(?:for|as|:|position)\s+(?:the\s+)?(?:position\s+of\s+)?([A-Za-z0-9\s/\-]+)",
            subject,
            re.IGNORECASE,
        )
        if match:
            position = match.group(1).strip()
            # Limit to reasonable length
            words = position.split()[:6]
            return " ".join(words).title()

        return None

    def _extract_position_from_body(self, body: str) -> Optional[str]:
        """Extract position from body.

        Args:
            body: Email body

        Returns:
            str: Position title or None
        """
        # Look for position indicators
        for indicator in POSITION_INDICATORS:
            pattern = rf"{re.escape(indicator)}\s+([A-Za-z0-9\s/\-]+)"
            match = re.search(pattern, body[:500], re.IGNORECASE)
            if match:
                position = match.group(1).strip()
                # Extract until punctuation
                position = re.split(r"[,\.\n]", position)[0]
                # Limit words
                words = position.split()[:6]
                if len(words) > 0:
                    return " ".join(words).title()

        return None

    def extract_all(self, email: Email) -> tuple[str, str]:
        """Extract both company and position.

        Args:
            email: Email object

        Returns:
            tuple: (company, position)
        """
        company = self.extract_company(email)
        position = self.extract_position(email)

        return company, position
