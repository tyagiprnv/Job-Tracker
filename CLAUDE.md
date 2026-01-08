# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Job Application Tracker is a Python CLI tool that automatically detects job-related emails from Gmail and tracks them in Google Sheets. It supports both English and German emails, uses sophisticated matching algorithms to link follow-up emails to existing applications, and prevents status downgrades.

## Essential Commands

### Installation & Setup
```bash
# Install dependencies
uv sync

# Create environment file
cp .env.example .env
# Then edit .env to add SPREADSHEET_ID

# Run the tracker (default: 60 days back)
uv run python main.py

# Run with custom date range
uv run python main.py --days 30

# Preview mode (no spreadsheet updates)
uv run python main.py --dry-run
```

### Google Cloud Setup Requirements
1. Create OAuth2 credentials (`credentials.json`) for Gmail API + Google Sheets API
2. Place `credentials.json` in project root
3. First run opens browser for OAuth consent, creates `token.json`
4. Get spreadsheet ID from Google Sheets URL and add to `.env`

## Architecture Overview

### Data Flow Pipeline
The application follows a **7-step pipeline architecture** (main.py:41-126):

1. **Fetch** (gmail/fetcher.py) - Retrieve emails from Gmail API
2. **Parse** (gmail/parser.py) - Extract sender, subject, body, thread_id from raw messages
3. **Detect** (detection/detector.py) - Score emails using weighted keyword matching (threshold: 5)
4. **Extract** (detection/extractor.py) - Pull company name and position from email content
5. **Classify** (detection/classifier.py) - Determine email type and status
6. **Match** (matching/matcher.py) - Link emails to existing applications using 4 strategies
7. **Update** (sheets/manager.py) - Create new or update existing spreadsheet rows

### Core Detection Algorithm

**Scoring System** (detection/detector.py:18-71):
- ATS domain (greenhouse.io, lever.co, etc.): +5 points
- Recruiting email patterns (recruiting@, talent@): +3 points
- Subject keywords: +2-3 points (weighted by confidence)
- Body keywords: +1-3 points (weighted by confidence)
- Job board domains: -3 points (reduces newsletter noise)
- **Threshold: Score ≥ 5 = job-related email**

**Exclusion filters** prevent false positives from newsletters and job alerts.

### Matching Strategies

**ApplicationMatcher uses 4 strategies in priority order** (matching/matcher.py:16-52):

1. **Thread ID Match** (100% confidence) - Same Gmail conversation thread
2. **Exact Match** (95% confidence) - Identical normalized company + position
3. **Fuzzy Match** (80-90% confidence) - Uses rapidfuzz with thresholds:
   - Company similarity ≥ 85%
   - Position similarity ≥ 75%
   - Combined weighted score ≥ 80%
4. **Recent Company Match** (70% confidence) - Same company within 30 days (only if exactly one match exists)

### Status Progression System

**Status updates follow strict rules** (sheets/manager.py:118-145):
- **Terminal statuses** (`Rejected`, `Withdrawn`, `Offer Received`) are never updated
- **No downgrades**: Status only moves forward in progression order defined in `config/settings.py:STATUS_VALUES`
- **Email metadata** (count, latest date, Gmail link) always updates even when status doesn't

### Data Models

**Email** (models/email.py) - Parsed Gmail message with:
- Core fields: message_id, thread_id, sender, subject, body, date
- Extracted fields: company, position, status, email_type, detection_score

**Application** (models/application.py) - Spreadsheet row representation with:
- Sheet fields: company, position, dates, status, email_count, gmail_link
- Tracking fields: row_number (for updates), thread_id (for matching)

### Configuration System

**config/keywords.py** contains:
- `ATS_DOMAINS` - Known applicant tracking systems
- `RECRUITING_PATTERNS` - Regex patterns for recruiting emails
- `STATUS_KEYWORDS` - Multilingual keywords for classification (English + German)
- `DETECTION_KEYWORDS` - Weighted keyword lists (high/medium/low confidence)

**config/settings.py** loads from `.env`:
- `DETECTION_THRESHOLD` (default: 5) - Minimum score for job detection
- `MATCHING_THRESHOLD` (default: 80) - Minimum fuzzy match score
- `GMAIL_SEARCH_DAYS` (default: 60) - How far back to search
- `STATUS_VALUES` - Ordered progression of application statuses
- `TERMINAL_STATUSES` - Statuses that prevent further updates

## Key Implementation Details

### Multilingual Support
All keywords in `config/keywords.py` include both English and German translations. No language detection is performed - all keywords work simultaneously. This approach is extensible to additional languages.

### OAuth2 Authentication
**Unified authentication** (config/settings.py:29-36) - Single token.json contains combined scopes for both Gmail (read-only) and Google Sheets APIs, reducing authentication friction.

### Gmail Thread Tracking
Thread IDs are preserved in applications to enable perfect matching of follow-up emails in the same conversation thread (matching/matcher.py:54-70).

### Company Name Normalization
`utils/text_utils.py` provides `normalize_company_name()` which strips common suffixes (Inc., LLC, GmbH, etc.) and normalizes whitespace for accurate matching.

## Common Adjustments

### Detection Too Strict/Loose
Edit `DETECTION_THRESHOLD` in `.env`:
- Lower (3-4): Catch more emails, possible false positives
- Higher (6-7): Stricter detection, may miss some emails

### Matching Too Strict/Loose
Edit `MATCHING_THRESHOLD` in `.env`:
- Lower (70-75): More aggressive matching, possible incorrect links
- Higher (85-90): Stricter matching, may create duplicate applications

### Adding New Status Types
1. Add to `STATUS_VALUES` list in `config/settings.py` (maintain progression order)
2. Add keywords to `STATUS_KEYWORDS` in `config/keywords.py`
3. Optionally add to `TERMINAL_STATUSES` if it should prevent updates

## File Organization

```
config/          # All configuration and keyword definitions
├── settings.py  # Environment variables, thresholds, constants
└── keywords.py  # Multilingual keywords, patterns, ATS domains

auth/            # OAuth2 authentication handlers
├── gmail_auth.py
└── sheets_auth.py

gmail/           # Gmail API integration
├── fetcher.py   # Retrieve emails via API
├── parser.py    # Parse raw messages into Email objects
└── client.py    # Low-level Gmail API wrapper

detection/       # Email analysis
├── detector.py  # Scoring algorithm for job detection
├── classifier.py # Determine email type and status
└── extractor.py # Extract company and position from text

matching/        # Application matching logic
└── matcher.py   # 4-strategy matching algorithm

sheets/          # Google Sheets integration
├── client.py    # Low-level Sheets API wrapper
└── manager.py   # High-level application CRUD operations

models/          # Data structures
├── email.py     # Email data model
└── application.py # Application data model

utils/           # Helper functions
└── text_utils.py # Text normalization and keyword matching

main.py          # CLI entry point and orchestration
```

## Testing and Debugging

Use `--dry-run` mode extensively when:
- Testing detection threshold changes
- Validating matching behavior
- Previewing what would be updated before committing to spreadsheet

The CLI output shows:
- Detection scores for understanding why emails matched/didn't match
- Matching confidence levels for troubleshooting duplicate applications
- Summary statistics for monitoring system performance
