# Job Application Tracker

Automatically track your job applications by reading Gmail and updating Google Sheets. Supports multilingual detection (English and German).

## Features

- **Dual Analysis Modes:**
  - **LLM Mode (default):** AI-powered analysis using DeepSeek API for highly accurate extraction
  - **Rules Mode:** Traditional keyword-based detection for offline/free usage
- Automatically detects job-related emails from Gmail
- Extracts company names and position titles
- Classifies email type (application received, interview, rejection, offer)
- Matches follow-up emails to existing applications
- Updates Google Sheets with application status
- Supports both English and German job emails
- Smart detection using ATS platforms, keywords, and patterns
- Prevents status downgrades and handles terminal statuses
- Beautiful CLI with progress indicators and summary tables

## Setup

### Prerequisites

- Python 3.13+
- Gmail account
- Google Cloud project with Gmail and Sheets APIs enabled

### 1. Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing one)

3. **Enable APIs:**
   - Navigate to "APIs & Services" > "Library"
   - Search for and enable:
     - Gmail API
     - Google Sheets API

4. **Configure OAuth Consent Screen:**
   - Go to "APIs & Services" > "OAuth consent screen"
   - Choose "External" user type
   - Fill in:
     - App name: "Job Application Tracker"
     - User support email: Your email
     - Developer contact: Your email
   - Add scopes:
     - `https://www.googleapis.com/auth/gmail.readonly`
     - `https://www.googleapis.com/auth/spreadsheets`
   - Add your email as a test user

5. **Create OAuth2 Credentials:**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Application type: "Desktop app"
   - Name: "Job Tracker Desktop"
   - Click "Create" and download the JSON file
   - **Rename the file to `credentials.json`**
   - **Place it in the project root directory**

### 2. Google Sheets Setup

1. Create a new Google Sheet
2. Name it "Job Applications Tracker" (or any name you prefer)
3. The script will automatically create headers on first run
4. Copy the Spreadsheet ID from the URL:
   ```
   https://docs.google.com/spreadsheets/d/[SPREADSHEET_ID]/edit
   ```

### 3. DeepSeek API Setup (Optional - for LLM mode)

**LLM mode** provides superior accuracy but requires a DeepSeek API key. **Rules mode** works offline without an API key.

1. Go to [DeepSeek Platform](https://platform.deepseek.com/)
2. Sign up and get your API key
3. Add credits to your account (~$0.01 per 100 emails, very affordable)

### 4. Project Setup

```bash
# Clone or navigate to the project
cd job-tracker

# Create .env file from template
cp .env.example .env

# Edit .env and add your configuration:
# - SPREADSHEET_ID: Your Google Sheet ID (required)
# - DEEPSEEK_API_KEY: Your DeepSeek API key (optional, for LLM mode)

# Install dependencies using uv
uv sync
```

### 5. First Run

```bash
# Run the tracker
uv run python main.py

# On first run:
# - Your browser will open for OAuth consent
# - Grant access to Gmail (read-only) and Google Sheets
# - The token will be saved in token.json for future runs
```

## Usage

### Basic Usage

```bash
# Run with LLM analysis (default - most accurate)
uv run python main.py

# Run with rules-based analysis (offline, free)
uv run python main.py --mode rules

# Search specific number of days back
uv run python main.py --days 30

# Preview mode (don't update spreadsheet)
uv run python main.py --dry-run

# Combine options
uv run python main.py --mode rules --days 15 --dry-run
```

### CLI Options

- `--mode`: Analysis mode - `llm` (AI-powered, default) or `rules` (traditional)
- `--days`: Number of days to search back for emails (default: 60)
- `--dry-run`: Preview mode - show what would be detected without updating the sheet
- `--reset-tracking`: Reset tracking files when switching spreadsheets (see below)
- `--help`: Show help message

### Choosing Between LLM and Rules Mode

**Use LLM Mode (default) when:**
- You want the highest accuracy (95%+ company names, 90%+ status)
- You want fewer false positives (marketplace emails filtered out)
- You have DeepSeek API credits (~$0.01 per 100 emails)
- You need context-aware analysis (rejection detection, ATS vs company names)

**Use Rules Mode when:**
- You want to run offline without API dependencies
- You prefer zero-cost operation
- You're okay with lower accuracy and some false positives
- You want faster processing (no API calls)

### Resetting Tracking Files (Switching Spreadsheets)

When switching to a new spreadsheet, tracking files from the old spreadsheet can cause all emails to be skipped. Use the reset command:

```bash
# Reset tracking files (deletes processed_emails.json and false_positives.json)
uv run python main.py --reset-tracking
```

**What gets reset:**
- `processed_emails.json` - Message IDs that have been processed (allows re-processing all emails)
- `false_positives.json` - Applications that were deleted (allows re-creating them)

**What is preserved:**
- `llm_cache.json` - LLM analysis cache (saves API costs on re-runs)

**When to use:**
- **Switching to a new spreadsheet** (change `SPREADSHEET_ID` in `.env`)
- **After updating detection logic** (code updates that improve email detection)
- **When confirmation emails were missed** (re-process to detect previously missed application confirmations)
- **Testing with a fresh slate** (verify detection and matching work correctly)
- **After manual spreadsheet cleanup** (removed rows should be recreated if still relevant)
- **When application dates are incorrect** (emails processed in wrong order, need reprocessing)

**After reset:**
Run normal processing to populate the spreadsheet with newly detected emails:
```bash
# Re-process last 60 days with improved detection
uv run python main.py --days 60

# Or test first with dry-run to preview changes
uv run python main.py --days 60 --dry-run
```

### Example Output

```
                    Job Application Tracker
                Scanning Gmail for job-related emails...

[LLM Mode] Loaded 490 cached results from llm_cache.json

Found 15 job-related emails

Summary:
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Metric                     ┃ Count ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ Total emails scanned       │   523 │
│ Job-related emails found   │    15 │
│ New applications created   │     8 │
│ Applications updated       │     7 │
│ LLM API calls made         │    33 │  (only new emails analyzed)
└────────────────────────────┴───────┘

✓ Successfully updated spreadsheet: 1abc123...
```

## Configuration

Edit `.env` to customize behavior:

```bash
# Google Sheets Configuration
SPREADSHEET_ID=your_spreadsheet_id_here

# DeepSeek API Configuration (for LLM mode)
DEEPSEEK_API_KEY=sk-your-api-key-here  # Get from platform.deepseek.com
DEEPSEEK_MODEL=deepseek-chat           # deepseek-chat or deepseek-coder
LLM_CACHE_FILE=llm_cache.json          # Path to persistent cache file

# Gmail Search Configuration
GMAIL_SEARCH_DAYS=60         # How many days back to search
GMAIL_MAX_RESULTS=500        # Maximum emails to process per run

# Detection Thresholds (for rules mode)
DETECTION_THRESHOLD=5        # Minimum score to consider job-related
MATCHING_THRESHOLD=80        # Minimum similarity for fuzzy matching

# Logging
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR
```

## How It Works

### LLM Analysis (Default Mode)

When using `--mode llm`, the tracker uses DeepSeek's AI model to analyze each email:

**Process:**
1. Extracts email subject, body (first 2000 chars), and sender
2. Sends to DeepSeek API with structured prompt
3. Receives JSON response with:
   - `is_job_related`: true/false classification
   - `company`: Actual employer name (not ATS platform)
   - `position`: Job title
   - `status`: Application status
   - `confidence`: 0.0-1.0 confidence score
   - `reasoning`: Explanation of classification

**Advantages:**
- Context-aware: Distinguishes marketplace emails from real applications
- Accurate company extraction: "Apple" not "Lever" or "Greenhouse"
- Better rejection detection: Understands subtle rejection language
- Multilingual by default: No separate rules for German
- Handles edge cases: Assessments from third parties, multi-thread applications

**Persistent Cache:**
- Results cached to `llm_cache.json` and persist across runs
- Cache loaded on startup - previously analyzed emails never re-analyzed
- Massive cost savings: Only new emails incur API costs
  - Day 1: 500 emails → $0.05
  - Day 2: 490 cached, 10 new → $0.001
  - Day 3: 498 cached, 2 new → $0.0002
- Survives `--reset-tracking` - cache is preserved when switching spreadsheets

**Fallback:** If API fails, automatically falls back to rules-based detection

### Rules-Based Detection (Traditional Mode)

When using `--mode rules`, the tracker uses a scoring system to identify job-related emails:

1. **ATS Platform Domains** (+5 points)
   - Greenhouse, Lever, Workday, iCIMS, SmartRecruiters, etc.

2. **Recruiting Email Patterns** (+3 points)
   - `recruiting@`, `talent@`, `careers@`, `bewerbung@` (German), etc.

3. **Subject Keywords** (+2-3 points)
   - "application", "interview", "offer"
   - "bewerbung", "vorstellungsgespräch", "zusage" (German)

4. **Body Keywords** (+1-3 points, weighted)
   - High confidence: "job application", "position you applied"
   - Medium confidence: "interview", "candidate", "recruiting team"
   - Low confidence: "opportunity", "role", "team"

**Threshold:** Score ≥ 5 = job-related email

### Matching Algorithm

Follow-up emails are matched to existing applications using:

1. **Thread ID Match** (100% confidence)
   - Same Gmail conversation thread

2. **Exact Match** (95% confidence)
   - Exact company name and position title

3. **Fuzzy Match** (80-90% confidence)
   - Similar company (≥85%) and position (≥75%)
   - Uses rapidfuzz library

4. **Recent Company Match** (70% confidence)
   - Same company within last 30 days (only if one application exists)

### Status Progression

Status transitions follow this progression:
```
Applied → Application Received → Interview Scheduled → Offer/Rejected
```

**Rules:**
- Status never downgrades (Interview → Applied is prevented)
- Terminal statuses (Rejected, Withdrawn, Offer Received) are not updated
- Preserves highest status achieved

### Multilingual Support

Fully supports both English and German job emails:

**English Keywords:**
- application received, interview scheduled, rejected, offer letter

**German Keywords:**
- bewerbung eingegangen, vorstellungsgespräch, absage, vertragsangebot

No language detection needed - all keywords work simultaneously.

## Spreadsheet Structure

| Column | Description | Example |
|--------|-------------|---------|
| Company | Company name | "Google" |
| Position | Job title | "Senior Software Engineer" |
| Application Date | Date first detected | "2026-01-08" |
| Current Status | Latest status | "Interview Scheduled" |
| Last Updated | Date of last change | "2026-01-10" |
| Email Count | Number of emails | 3 |
| Latest Email Date | Most recent email | "2026-01-10" |
| Notes | Auto-extracted info | "" |
| Gmail Link | Link to latest email | gmail.com/mail/... |

## Troubleshooting

### "credentials.json not found"

Download OAuth2 credentials from Google Cloud Console and place in project root.

### "Spreadsheet not found"

Check that `SPREADSHEET_ID` in `.env` matches your Google Sheet ID.

### "Rate limit exceeded"

The script handles rate limits automatically with exponential backoff. If it persists, reduce `GMAIL_MAX_RESULTS`.

### No job emails detected

Try adjusting `DETECTION_THRESHOLD` in `.env` to a lower value (e.g., 3-4) to catch more emails.

### False positives

Increase `DETECTION_THRESHOLD` to be more strict (e.g., 6-7) or use `--mode llm` for better accuracy.

### "Warning: DEEPSEEK_API_KEY not set"

If using LLM mode, add your DeepSeek API key to `.env`. Or use `--mode rules` to run without API key.

### Managing LLM Cache

The LLM cache grows over time as new emails are analyzed. To manage:

```bash
# View cache size
ls -lh llm_cache.json

# Clear cache (force re-analysis of all emails)
rm llm_cache.json

# Note: Cache is preserved during --reset-tracking
# Delete manually if you want to force re-analysis
```

**When to clear the cache:**
- Testing LLM prompt changes (want to see new analysis results)
- Corrupted cache file (parser errors)
- Want to use updated LLM model on old emails

**Cost impact:** Clearing cache means all emails will be re-analyzed on next run, incurring API costs again (~$0.01 per 100 emails).

## Project Structure

```
job-tracker/
├── main.py                 # CLI entry point
├── config/                 # Configuration and keywords
├── auth/                   # OAuth2 authentication
├── gmail/                  # Gmail API integration
├── llm/                    # LLM-based analysis (DeepSeek)
│   ├── deepseek_client.py  # API client
│   ├── prompts.py          # Prompt templates
│   └── email_analyzer.py   # Main LLM analyzer
├── detection/              # Rules-based detection and classification
├── sheets/                 # Google Sheets integration
├── matching/               # Application matching logic
├── models/                 # Data models
└── utils/                  # Utility functions

# Auto-generated files (in .gitignore):
├── credentials.json         # OAuth2 credentials (manual download from GCP)
├── token.json              # OAuth2 access tokens (auto-generated on first run)
├── llm_cache.json          # LLM analysis cache (auto-generated, persistent)
├── processed_emails.json   # Processed message IDs (use --reset-tracking to clear)
└── false_positives.json    # False positives tracker (use --reset-tracking to clear)
```

## Contributing

This is a personal project, but feel free to fork and customize for your needs.

## License

MIT License - feel free to use and modify as needed.

## Privacy & Security

- **Read-only Gmail access:** The app only reads emails, never sends or modifies them
- **Local credentials:** OAuth tokens are stored locally in `token.json`
- **No data sharing:** All data stays between your Gmail and your Google Sheet
- **Credentials in .gitignore:** Secrets are never committed to version control

## Future Enhancements

Potential improvements:
- Scheduled/automated runs (cron job)
- Email notifications for new applications
- Statistics dashboard
- Browser extension for quick-add from job sites
- Multi-user support
- Integration with other email providers