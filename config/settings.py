"""Configuration settings for job tracker."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Google Sheets Configuration
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "")
if not SPREADSHEET_ID:
    print("Warning: SPREADSHEET_ID not set in .env file")

# Gmail Configuration
GMAIL_SEARCH_DAYS = int(os.getenv("GMAIL_SEARCH_DAYS", "60"))
GMAIL_MAX_RESULTS = int(os.getenv("GMAIL_MAX_RESULTS", "500"))

# Detection Thresholds
DETECTION_THRESHOLD = int(os.getenv("DETECTION_THRESHOLD", "5"))
MATCHING_THRESHOLD = int(os.getenv("MATCHING_THRESHOLD", "80"))

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# DeepSeek API Configuration
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

if not DEEPSEEK_API_KEY:
    print("Warning: DEEPSEEK_API_KEY not set in .env file")

# OAuth2 Scopes (combined for single authentication)
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
ALL_SCOPES = GMAIL_SCOPES + SHEETS_SCOPES

# File paths for OAuth2 credentials and tokens
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
GMAIL_TOKEN_FILE = PROJECT_ROOT / "token.json"

# LLM cache file path
LLM_CACHE_FILE = PROJECT_ROOT / "llm_cache.json"

# False positives tracking file
FALSE_POSITIVES_FILE = PROJECT_ROOT / "false_positives.json"

# Processed emails tracking file (prevents double-counting)
PROCESSED_EMAILS_FILE = PROJECT_ROOT / "processed_emails.json"

# Sheet column definitions
SHEET_COLUMNS = [
    "Company",
    "Position",
    "Application Date",
    "Current Status",
    "Last Updated",
    "Email Count",
    "Latest Email Date",
    "Notes",
    "Gmail Link",
]

# Status values (ordered by progression)
STATUS_VALUES = [
    "Applied",
    "Application Received",
    "Under Review",
    "Phone Screen Scheduled",
    "Interview Scheduled",
    "Assessment Sent",
    "Offer Received",
    "Rejected",
    "Withdrawn",
]

# Terminal statuses (no further updates)
TERMINAL_STATUSES = ["Rejected", "Withdrawn", "Offer Received"]
