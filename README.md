# Job Application Tracker

Automatically track your job applications by reading Gmail and updating Google Sheets. Supports multilingual detection (English and German).

## Features

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

### 3. Project Setup

```bash
# Clone or navigate to the project
cd job-tracker

# Create .env file from template
cp .env.example .env

# Edit .env and add your spreadsheet ID
# SPREADSHEET_ID=your_spreadsheet_id_here

# Install dependencies using uv
uv sync
```

### 4. First Run

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
# Run the tracker (default: last 60 days)
uv run python main.py

# Search specific number of days back
uv run python main.py --days 30

# Preview mode (don't update spreadsheet)
uv run python main.py --dry-run
```

### CLI Options

- `--days`: Number of days to search back for emails (default: 60)
- `--dry-run`: Preview mode - show what would be detected without updating the sheet
- `--help`: Show help message

### Example Output

```
                    Job Application Tracker
                Scanning Gmail for job-related emails...

Found 15 job-related emails

Summary:
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Metric                     ┃ Count ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ Total emails scanned       │   523 │
│ Job-related emails found   │    15 │
│ New applications created   │     8 │
│ Applications updated       │     7 │
└────────────────────────────┴───────┘

✓ Successfully updated spreadsheet: 1abc123...
```

## Configuration

Edit `.env` to customize behavior:

```bash
# Google Sheets Configuration
SPREADSHEET_ID=your_spreadsheet_id_here

# Gmail Search Configuration
GMAIL_SEARCH_DAYS=60         # How many days back to search
GMAIL_MAX_RESULTS=500        # Maximum emails to process per run

# Detection Thresholds
DETECTION_THRESHOLD=5        # Minimum score to consider job-related
MATCHING_THRESHOLD=80        # Minimum similarity for fuzzy matching

# Logging
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR
```

## How It Works

### Detection Algorithm

The tracker uses a scoring system to identify job-related emails:

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

Increase `DETECTION_THRESHOLD` to be more strict (e.g., 6-7).

## Project Structure

```
job-tracker/
├── main.py                 # CLI entry point
├── config/                 # Configuration and keywords
├── auth/                   # OAuth2 authentication
├── gmail/                  # Gmail API integration
├── detection/              # Email detection and classification
├── sheets/                 # Google Sheets integration
├── matching/               # Application matching logic
├── models/                 # Data models
└── utils/                  # Utility functions
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