# Job Application Tracker

Automatically track your job applications by reading Gmail and updating Google Sheets.

## Features

- **Dual Analysis Modes:**
  - **LLM Mode (default):** AI-powered analysis using DeepSeek API (~$0.01/100 emails, highly accurate)
  - **Rules Mode:** Keyword-based detection (offline, free, lower accuracy)
- **Smart Gmail Filtering:** Only processes primary inbox emails (excludes promotions/social tabs)
- **Intelligent Matching:** Links follow-up emails to existing applications using thread IDs and fuzzy matching
- **Status Tracking:** Automatically classifies emails (applied, interview, rejection, offer) with no downgrades
- **Multilingual:** Supports English and German emails
- **Persistent Cache:** LLM results cached - only new emails analyzed (massive cost savings)

## Quick Start

### 1. Install Dependencies
```bash
uv sync
```

### 2. Google Cloud Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/) and create a project
2. Enable **Gmail API** and **Google Sheets API** (APIs & Services > Library)
3. Create **OAuth2 credentials**:
   - APIs & Services > Credentials > Create Credentials > OAuth client ID
   - Type: Desktop app
   - Download JSON and rename to `credentials.json` in project root
4. Configure **OAuth consent screen**:
   - User type: External
   - Add scopes: `gmail.readonly` and `spreadsheets`
   - Add your email as test user

### 3. Create Google Sheet
1. Create a new Google Sheet (headers auto-generated on first run)
2. Copy the Spreadsheet ID from URL: `docs.google.com/spreadsheets/d/[SPREADSHEET_ID]/edit`

### 4. Configure Environment
```bash
cp .env.example .env
# Edit .env and add:
# - SPREADSHEET_ID (required)
# - DEEPSEEK_API_KEY (optional, for LLM mode - get from platform.deepseek.com)
```

### 5. Run
```bash
uv run python main.py
# Browser opens for OAuth consent on first run
```

## Usage

```bash
# Default: LLM mode, last 60 days
uv run python main.py

# Rules mode (offline, free)
uv run python main.py --mode rules

# Custom date range
uv run python main.py --days 30

# Preview without updating (dry-run)
uv run python main.py --dry-run

# Reset tracking (when switching spreadsheets)
uv run python main.py --reset-tracking
```

### CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--mode llm\|rules` | Analysis mode: AI-powered or keyword-based | `llm` |
| `--days N` | Days to search back | `60` |
| `--dry-run` | Preview only, don't update sheet | - |
| `--reset-tracking` | Clear processed email tracking | - |

**LLM vs Rules Mode:**
- **LLM:** Higher accuracy (95%+), context-aware, costs ~$0.01/100 emails (cached emails free)
- **Rules:** Offline, free, faster, but lower accuracy and more false positives

## Configuration

Key settings in `.env`:

```bash
# Required
SPREADSHEET_ID=your_spreadsheet_id_here

# Optional (LLM mode)
DEEPSEEK_API_KEY=sk-your-key-here      # From platform.deepseek.com

# Tuning (optional)
GMAIL_SEARCH_DAYS=60                   # Days to search back
DETECTION_THRESHOLD=5                  # Rules mode: min score (lower = more emails)
MATCHING_THRESHOLD=80                  # Fuzzy match threshold (lower = more aggressive)
```

## How It Works

### Pipeline
1. **Fetch** - Query Gmail (primary inbox only, excludes promotions/social tabs)
2. **Analyze** - LLM extracts job details OR rules-based scoring
3. **Match** - Link to existing applications via thread ID or fuzzy matching
4. **Update** - Create/update Google Sheets rows with status progression

### LLM Mode (Default)
- Sends email to DeepSeek API with structured prompt
- Returns: company, position, status, confidence, reasoning
- **Persistent cache** (`llm_cache.json`) - previously analyzed emails never re-analyzed
- Accurately extracts actual company name (not ATS platform like "Greenhouse")
- Context-aware rejection detection, multilingual by default

### Rules Mode
- Scores emails using weighted keywords and ATS domain detection
- Threshold: Score ≥ 5 = job-related
- Faster but less accurate than LLM mode

### Matching
1. **Thread ID** (100%) - Same Gmail thread
2. **Exact** (95%) - Identical company + position
3. **Fuzzy** (80-90%) - Similar company (≥85%) + position (≥75%)
4. **Recent** (70%) - Same company within 30 days (if single match)

### Status Progression
- Forward-only: `Applied → Received → Interview → Offer/Rejected`
- Terminal statuses (Rejected, Withdrawn, Offer) never updated

## Spreadsheet Structure

| Column | Description |
|--------|-------------|
| Company | Company name extracted from email |
| Position | Job title |
| Application Date | First email date |
| Current Status | Latest status (Applied/Received/Interview/Rejected/Offer) |
| Last Updated | Date of last status change |
| Email Count | Number of related emails |
| Latest Email Date | Most recent email in thread |
| Gmail Link | Direct link to latest email |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `credentials.json not found` | Download OAuth2 credentials from Google Cloud Console |
| `Spreadsheet not found` | Verify `SPREADSHEET_ID` in `.env` matches your Sheet ID |
| No emails detected | Lower `DETECTION_THRESHOLD` (e.g., 3-4) or use `--mode llm` |
| Too many false positives | Raise `DETECTION_THRESHOLD` (e.g., 6-7) or use `--mode llm` |
| `DEEPSEEK_API_KEY not set` | Add API key to `.env` or use `--mode rules` |
| Rate limit errors | Script auto-retries; if persists, reduce `GMAIL_MAX_RESULTS` |
| Emails skipped after spreadsheet switch | Run `--reset-tracking` to clear processed email cache |

## Project Structure

```
job-tracker/
├── main.py                  # CLI entry point
├── gmail/                   # Gmail API (fetcher, parser, client)
├── llm/                     # DeepSeek AI analysis (analyzer, prompts, client)
├── detection/               # Rules-based analysis (detector, classifier, extractor)
├── matching/                # Application matching strategies
├── sheets/                  # Google Sheets integration
├── config/                  # Settings and keywords
└── models/                  # Email and Application data models

# Auto-generated files (gitignored):
├── credentials.json         # OAuth2 creds (download from GCP)
├── token.json              # OAuth2 tokens (auto-created)
├── llm_cache.json          # LLM analysis cache (persistent)
├── processed_emails.json   # Processed IDs (--reset-tracking to clear)
└── false_positives.json    # Deleted apps tracker (--reset-tracking to clear)
```

## Privacy & Security

- Read-only Gmail access (never sends/modifies emails)
- Local OAuth tokens only
- No external data sharing (Gmail ↔ Google Sheets only)
- All credentials gitignored

## License

MIT License