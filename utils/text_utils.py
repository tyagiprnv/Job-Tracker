"""Text processing utilities."""

import re
from config.keywords import COMPANY_SUFFIXES


def normalize_text(text: str) -> str:
    """Normalize text for comparison (lowercase, trim whitespace)."""
    if not text:
        return ""
    return " ".join(text.lower().strip().split())


def normalize_company_name(company: str) -> str:
    """Normalize company name for matching."""
    if not company:
        return ""

    # Convert to lowercase and strip
    normalized = company.lower().strip()

    # Remove common suffixes
    for suffix in COMPANY_SUFFIXES:
        # Match suffix at end of string with optional period and spaces
        pattern = rf"\s+{re.escape(suffix)}\.?\s*$"
        normalized = re.sub(pattern, "", normalized, flags=re.IGNORECASE)

    # Remove extra whitespace
    normalized = " ".join(normalized.split())

    return normalized


def extract_email_domain(email: str) -> str:
    """Extract domain from email address."""
    if not email or "@" not in email:
        return ""

    # Remove angle brackets if present (e.g., "Name <email@domain.com>")
    email = re.search(r"[\w\.-]+@[\w\.-]+", email)
    if not email:
        return ""

    domain = email.group(0).split("@")[1].lower()
    return domain


def extract_email_address(sender_field: str) -> str:
    """Extract email address from sender field."""
    if not sender_field:
        return ""

    # Match email pattern
    match = re.search(r"[\w\.-]+@[\w\.-]+", sender_field)
    if match:
        return match.group(0).lower()

    return sender_field.lower()


def extract_sender_name(sender_field: str) -> str:
    """Extract sender name from sender field."""
    if not sender_field:
        return ""

    # Try to extract name before email in angle brackets
    match = re.match(r"([^<]+)\s*<", sender_field)
    if match:
        name = match.group(1).strip()
        # Remove quotes if present
        name = name.strip('"').strip("'")
        return name

    # If no angle brackets, return the part before @
    if "@" in sender_field:
        return sender_field.split("@")[0]

    return sender_field


def clean_html_text(text: str) -> str:
    """Clean text that might contain HTML remnants."""
    if not text:
        return ""

    # Remove common HTML entities
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&quot;", '"', text)

    # Remove extra whitespace
    text = " ".join(text.split())

    return text


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to maximum length with ellipsis."""
    if not text or len(text) <= max_length:
        return text

    return text[: max_length - 3] + "..."


def contains_any_keyword(text: str, keywords: list[str]) -> bool:
    """Check if text contains any of the keywords (case-insensitive)."""
    if not text:
        return False

    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in keywords)


def extract_domain_company_name(domain: str) -> str:
    """Extract company name from domain (e.g., 'careers.google.com' -> 'google')."""
    if not domain:
        return ""

    # Remove common subdomains
    domain = re.sub(r"^(www|mail|careers|jobs|recruiting|talent)\.", "", domain)

    # Get the main part (before TLD)
    parts = domain.split(".")
    if len(parts) >= 2:
        # Return second-to-last part (company name)
        return parts[-2]

    return domain
