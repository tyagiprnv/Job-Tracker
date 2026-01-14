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

# LLM Provider Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "").lower()
LLM_MODEL = os.getenv("LLM_MODEL", "")

# Provider-specific API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# Backward compatibility: Auto-detect provider from API key if not explicitly set
if not LLM_PROVIDER:
    if DEEPSEEK_API_KEY:
        LLM_PROVIDER = "deepseek"
        print("Info: Using DeepSeek provider (legacy DEEPSEEK_API_KEY detected)")
        print("Tip: Set LLM_PROVIDER=deepseek in .env for explicit configuration")
    elif OPENAI_API_KEY:
        LLM_PROVIDER = "openai"
    elif ANTHROPIC_API_KEY:
        LLM_PROVIDER = "anthropic"
    elif GOOGLE_API_KEY:
        LLM_PROVIDER = "google"

# Provider defaults (model names used if LLM_MODEL not specified)
PROVIDER_DEFAULTS = {
    "openai": {
        "model": "gpt-4o-mini",
        "cost_per_100": "$0.30",
        "env_var": "OPENAI_API_KEY"
    },
    "anthropic": {
        "model": "claude-3-5-haiku-20241022",
        "cost_per_100": "$0.25",
        "env_var": "ANTHROPIC_API_KEY"
    },
    "google": {
        "model": "gemini-1.5-flash",
        "cost_per_100": "$0.15",
        "env_var": "GOOGLE_API_KEY"
    },
    "deepseek": {
        "model": "deepseek/deepseek-chat",
        "cost_per_100": "$0.01",
        "env_var": "DEEPSEEK_API_KEY"
    }
}

# Get final model name (user override or provider default)
if not LLM_MODEL and LLM_PROVIDER:
    LLM_MODEL = PROVIDER_DEFAULTS.get(LLM_PROVIDER, {}).get("model", "")


def validate_llm_config():
    """Validate LLM configuration at startup.

    Returns:
        tuple: (is_valid, error_message, warning_message)
    """
    if not LLM_PROVIDER:
        return (False, "No LLM provider configured. Set LLM_PROVIDER in .env or provide an API key.", None)

    if LLM_PROVIDER not in PROVIDER_DEFAULTS:
        valid_providers = ", ".join(PROVIDER_DEFAULTS.keys())
        return (False, f"Invalid LLM_PROVIDER: {LLM_PROVIDER}. Valid options: {valid_providers}", None)

    # Check if corresponding API key is set
    provider_config = PROVIDER_DEFAULTS[LLM_PROVIDER]
    api_key_var = provider_config["env_var"]
    api_key_value = globals().get(api_key_var, "")

    if not api_key_value:
        return (False, f"{api_key_var} not set in .env file. Required for {LLM_PROVIDER} provider.", None)

    # Cost warning for expensive providers
    warning = None
    if LLM_PROVIDER in ["openai", "anthropic", "google"]:
        deepseek_cost = PROVIDER_DEFAULTS["deepseek"]["cost_per_100"]
        provider_cost = provider_config["cost_per_100"]
        warning = (
            f"\nCost Notice: {LLM_PROVIDER.upper()} costs ~{provider_cost}/100 emails "
            f"vs DeepSeek {deepseek_cost}/100 emails.\n"
            f"Consider using --mode rules for offline/free analysis."
        )

    return (True, None, warning)

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

# Merged applications tracking file (tracks merged thread IDs)
MERGED_APPLICATIONS_FILE = PROJECT_ROOT / "merged_applications.json"

# Conflict resolutions tracking file (tracks user HITL decisions)
CONFLICT_RESOLUTIONS_FILE = PROJECT_ROOT / "conflict_resolutions.json"

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
    "Thread ID",
    "Merge Into Row",
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
