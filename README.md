# Job Application Tracker

Automatically track job applications by reading Gmail and updating Google Sheets with AI-powered analysis.

## Features

- **Dual Analysis Modes:** AI-powered (LLM) with 4 providers or keyword-based (rules) for offline use
- **Conflict Resolution:** Interactive prompts when emails conflict with spreadsheet data, with learning to auto-apply past decisions
- **Smart Matching:** Links follow-up emails using thread IDs and fuzzy matching (4 strategies)
- **Manual Merge:** Consolidate duplicate applications directly from spreadsheet
- **Status Progression:** Forward-only status updates (Applied → Interview → Offer/Rejected)
- **Multilingual:** Native support for English and German
- **Persistent Cache:** Only new emails incur API costs (~$0.01 per 100 emails with DeepSeek)

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
# Edit .env:
# - SPREADSHEET_ID (required)
# - For LLM mode (optional): Set LLM_PROVIDER (openai/anthropic/google/deepseek) + API key
# - Or use --mode rules for offline operation (no API needed)
```

### 5. Run
```bash
uv run python main.py
# Browser opens for OAuth consent on first run
```

## Usage

```bash
# Default: LLM mode, last 60 days, interactive
uv run python main.py

# Rules mode (offline, free)
uv run python main.py --mode rules

# Non-interactive mode (auto-resolve conflicts)
uv run python main.py --non-interactive

# Custom date range
uv run python main.py --days 30

# Preview without updating
uv run python main.py --dry-run

# Reset tracking (switching spreadsheets/clear learned resolutions)
uv run python main.py --reset-tracking
```

### CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--mode llm\|rules` | Analysis mode: AI-powered or keyword-based | `llm` |
| `--days N` | Days to search back | `60` |
| `--dry-run` | Preview only, no spreadsheet updates | - |
| `--non-interactive` | Auto-resolve conflicts (keep spreadsheet values) | - |
| `--reset-tracking` | Clear tracking and learned resolutions | - |

**Mode Comparison:**
- **LLM:** 95%+ accuracy, context-aware, ~$0.01/100 new emails (DeepSeek)
- **Rules:** Offline, free, faster, but lower accuracy

## Manual Merging

Consolidate duplicate applications directly in the spreadsheet:

1. Enter target row number in "Merge Into Row" column (column 11)
2. Run the script - merges execute before processing new emails
3. Source row automatically deleted after successful merge

**Example:** Row 15, column 11 → enter "8" → row 15 merges into row 8

**Merge logic:**
- Date: Earliest | Status: Most progressed | Emails: Sum | Link: Latest
- Notes: Combined with " | " separator
- Thread IDs: Combined (future emails match either thread)

**Validation:** Prevents self-merge, circular merges, chain merges, invalid targets

**Preview:** Use `--dry-run` to preview merges without executing

## Conflict Resolution

When an email has different company/position info than the spreadsheet, you'll see an interactive prompt:

**Options:**
1. Keep spreadsheet values
2. Use email values
3. Choose individually per field
4. Create separate entry (new application)

**Learning System:**
- Your decisions are saved and automatically applied to identical future conflicts
- Example: If you choose "Google" over "Google Inc." once, that choice is auto-applied next time
- Clear learned decisions: `uv run python main.py --reset-tracking`
- Use `--non-interactive` to skip prompts (always keeps spreadsheet values)

## Configuration

Key settings in `.env`:

```bash
# Required
SPREADSHEET_ID=your_spreadsheet_id_here

# LLM Mode Configuration (optional)
LLM_PROVIDER=deepseek              # Options: openai, anthropic, google, deepseek
DEEPSEEK_API_KEY=sk-...           # Or OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY

# Advanced: Override default model
# LLM_MODEL=gpt-4o-mini           # For custom model selection

# Tuning (optional)
GMAIL_SEARCH_DAYS=60                   # Days to search back
DETECTION_THRESHOLD=5                  # Rules mode: min score (lower = more emails)
MATCHING_THRESHOLD=80                  # Fuzzy match threshold (lower = more aggressive)
```

### LLM Provider Comparison

| Provider | Cost/100 emails | Speed | JSON Mode | API Key Source |
|----------|----------------|-------|-----------|----------------|
| DeepSeek | ~$0.01 | Fast | Native | platform.deepseek.com |
| Google Gemini | ~$0.15 | Fast | Native | makersuite.google.com |
| Anthropic Claude | ~$0.25 | Medium | Prompt-based | console.anthropic.com |
| OpenAI GPT | ~$0.30 | Medium | Native | platform.openai.com |

**Recommendation:** Start with DeepSeek for best cost/performance ratio.

## How It Works

**Pipeline:**
1. **Fetch** - Gmail (primary inbox only, excludes promotions/social)
2. **Merge** - Execute manual merge requests from spreadsheet
3. **Analyze** - LLM extraction or rules-based scoring
4. **Match** - Link to existing applications (4 strategies, checks merged thread IDs)
5. **Conflict Check** - Detect company/position mismatches
6. **Resolve** - Interactive prompts or auto-apply saved decisions
7. **Update** - Create/update spreadsheet with forward-only status progression

**LLM Mode (Default):**
- Structured prompt → LLM API → JSON response (company, position, status, confidence, reasoning)
- Persistent cache (`llm_cache.json`) - analyzed emails never re-analyzed, even across provider switches
- Context-aware: distinguishes real applications from job alerts, extracts employer (not ATS platform)

**Rules Mode:**
- Weighted keyword scoring + ATS domain detection (threshold: ≥5 points = job-related)
- Offline, free, faster, but lower accuracy

**Matching Strategies:**
1. Thread ID (100%) - Same Gmail conversation
2. Exact (95%) - Identical company + position
3. Fuzzy (80-90%) - Company ≥85% + position ≥75% similar
4. Recent (70%) - Same company within 30 days (single match only)

## Spreadsheet Structure

Headers are auto-generated on first run:

| Column | Description |
|--------|-------------|
| Company | Company name |
| Position | Job title |
| Application Date | First email date |
| Current Status | Latest status (forward-only progression) |
| Last Updated | Date of last status change |
| Email Count | Number of related emails |
| Latest Email Date | Most recent email date |
| Gmail Link | Direct link to latest email |
| Notes | Additional information (merged via " \| ") |
| Merge Into Row | Enter target row # to merge (column 11) |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `credentials.json not found` | Download OAuth2 credentials from Google Cloud Console |
| `Spreadsheet not found` | Verify `SPREADSHEET_ID` in `.env` matches Sheet ID |
| No emails detected | Use `--mode llm` or lower `DETECTION_THRESHOLD` (e.g., 3-4) |
| Too many false positives | Use `--mode llm` or raise `DETECTION_THRESHOLD` (e.g., 6-7) |
| Too many conflict prompts | Use `--non-interactive` or let system learn from your decisions |
| Wrong auto-resolution | Run `--reset-tracking` to clear learned decisions |
| Emails skipped after switching sheets | Run `--reset-tracking` to clear processed email cache |
| `LLM Configuration Error` | Set `LLM_PROVIDER` + API key in `.env` or use `--mode rules` |
| Rate limits | Script auto-retries; reduce `GMAIL_MAX_RESULTS` if persists |

## Project Structure

```
job-tracker/
├── main.py                          # CLI entry point
├── config/                          # Settings and keywords
├── auth/                            # OAuth2 authentication
├── gmail/                           # Gmail API (fetcher, parser, client)
├── llm/                             # Multi-provider LLM analysis
├── detection/                       # Rules-based analysis
├── matching/                        # Application matching (4 strategies)
├── sheets/                          # Google Sheets + merge manager
├── hitl/                            # Conflict detection and resolution
├── tracking/                        # State trackers (emails, merges, conflicts)
├── models/                          # Data structures (Email, Application)
└── utils/                           # Text utilities

# Auto-generated files (gitignored):
├── credentials.json                 # OAuth2 creds (from Google Cloud Console)
├── token.json                       # OAuth2 tokens (auto-created)
├── llm_cache.json                   # LLM analysis cache
├── processed_emails.json            # Processed IDs
├── false_positives.json             # Deleted apps
├── merged_applications.json         # Merge history
└── conflict_resolutions.json        # Learned conflict decisions
```

## Privacy & Security

- **Read-only Gmail access** - never sends or modifies emails
- **Local-only** - OAuth tokens stored locally, all credentials gitignored
- **Data flow** - Gmail → Local analysis → Google Sheets (no external sharing)
- **LLM mode** - Email metadata sent to chosen provider API (subject, body excerpt, sender)

## License

MIT