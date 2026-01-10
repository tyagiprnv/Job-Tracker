# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Job Application Tracker is a Python CLI tool that automatically detects job-related emails from Gmail and tracks them in Google Sheets. It features **dual analysis modes**: AI-powered LLM analysis (default) for high accuracy, and traditional rules-based analysis for offline/free usage. Supports both English and German emails, uses sophisticated matching algorithms to link follow-up emails to existing applications, and prevents status downgrades.

## Essential Commands

### Installation & Setup
```bash
# Install dependencies
uv sync

# Create environment file
cp .env.example .env
# Then edit .env to add SPREADSHEET_ID and LLM_PROVIDER with API key (for LLM mode)

# Run with LLM analysis (default - most accurate)
uv run python main.py

# Run with rules-based analysis (offline, free)
uv run python main.py --mode rules

# Run with custom date range
uv run python main.py --days 30

# Preview mode (no spreadsheet updates)
uv run python main.py --dry-run

# Reset tracking files (use when switching spreadsheets)
uv run python main.py --reset-tracking

# Combine options
uv run python main.py --mode llm --days 15 --dry-run
```

### Google Cloud Setup Requirements
1. Create OAuth2 credentials (`credentials.json`) for Gmail API + Google Sheets API
2. Place `credentials.json` in project root
3. First run opens browser for OAuth consent, creates `token.json`
4. Get spreadsheet ID from Google Sheets URL and add to `.env`

### LLM API Setup (Optional - for LLM mode)

The tool supports 4 LLM providers for AI-powered email analysis:

**1. DeepSeek (Recommended - Most Cost-Effective)**
- Sign up at https://platform.deepseek.com/
- Cost: ~$0.01 per 100 emails
- Add to `.env`: `LLM_PROVIDER=deepseek` and `DEEPSEEK_API_KEY=sk-...`

**2. OpenAI**
- Get API key from https://platform.openai.com/
- Cost: ~$0.30 per 100 emails (30x more than DeepSeek)
- Add to `.env`: `LLM_PROVIDER=openai` and `OPENAI_API_KEY=sk-...`

**3. Anthropic**
- Get API key from https://console.anthropic.com/
- Cost: ~$0.25 per 100 emails
- Add to `.env`: `LLM_PROVIDER=anthropic` and `ANTHROPIC_API_KEY=sk-ant-...`

**4. Google (Gemini)**
- Get API key from https://makersuite.google.com/app/apikey
- Cost: ~$0.15 per 100 emails
- Add to `.env`: `LLM_PROVIDER=google` and `GOOGLE_API_KEY=...`

**Or run without API (free, offline):**
- Use `--mode rules` for traditional keyword-based detection

## Architecture Overview

### Data Flow Pipeline

The application follows a pipeline architecture with **two analysis modes** (main.py:80-106):

**Common Steps (both modes):**
1. **Fetch** (gmail/fetcher.py) - Retrieve emails from Gmail API
2. **Parse** (gmail/parser.py) - Extract sender, subject, body, thread_id from raw messages

**LLM Mode Pipeline** (`--mode llm`, default):
3. **Analyze** (llm/email_analyzer.py) - Single LLM call per email extracts:
   - Job-related classification
   - Company name (actual employer, not ATS)
   - Position title
   - Application status
   - Confidence score and reasoning
4. **Match** (matching/matcher.py) - Link emails to existing applications
5. **Update** (sheets/manager.py) - Create new or update existing spreadsheet rows

**Rules Mode Pipeline** (`--mode rules`):
3. **Detect** (detection/detector.py) - Score emails using weighted keyword matching (threshold: 5)
4. **Extract** (detection/extractor.py) - Pull company name and position using regex
5. **Classify** (detection/classifier.py) - Determine email type and status using keywords
6. **Match** (matching/matcher.py) - Link emails to existing applications
7. **Update** (sheets/manager.py) - Create new or update existing spreadsheet rows

### LLM Analysis (Default Mode)

**Multi-Provider LLM Integration** (llm/llm_client.py):
- Uses LiteLLM library for unified provider interface
- Supports: OpenAI, Anthropic, Google, DeepSeek
- Sends email subject, body (first 2000 chars), and sender to chosen LLM API
- Uses structured prompt with examples (llm/prompts.py)
- Receives JSON response with: `is_job_related`, `company`, `position`, `status`, `confidence`, `reasoning`
- Low temperature (0.1) for consistent, deterministic results
- Provider-specific JSON mode handling (OpenAI/Google native, Anthropic prompt-based)

**Advantages over rules-based:**
- Context-aware: Distinguishes marketplace/promotional emails from real applications
- Accurate company extraction: Identifies actual employer vs ATS platform name
- Better rejection detection: Understands subtle rejection language
- Multilingual by default: No separate rules for German
- Handles edge cases: Third-party assessments, multi-thread applications

**Fallback Strategy** (llm/email_analyzer.py:118-142):
- If LLM API fails, automatically falls back to rules-based detection
- Ensures system reliability even without API availability

**Persistent Cache** (llm/email_analyzer.py:159-184):
- Results cached to `llm_cache.json` and persist across runs
- Cache loaded on startup - previously analyzed emails never re-analyzed
- Saves after each new analysis to prevent data loss
- Massive cost savings: Only new emails incur API costs
  - Day 1: 500 emails → $0.05
  - Day 2: 490 cached, 10 new → $0.001
  - Day 3: 498 cached, 2 new → $0.0002
- Gracefully handles missing or corrupted cache files

### Core Detection Algorithm (Rules Mode)

**Scoring System** (detection/detector.py:18-71) - Used when `--mode rules`:
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
- `LLM_PROVIDER` - LLM provider to use (openai, anthropic, google, deepseek)
- `LLM_MODEL` - Model name override (optional, uses provider defaults)
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `DEEPSEEK_API_KEY` - API keys
- `LLM_CACHE_FILE` - Path to persistent cache file (llm_cache.json)
- `DETECTION_THRESHOLD` (default: 5) - Minimum score for job detection (rules mode)
- `MATCHING_THRESHOLD` (default: 80) - Minimum fuzzy match score
- `GMAIL_SEARCH_DAYS` (default: 60) - How far back to search
- `STATUS_VALUES` - Ordered progression of application statuses
- `TERMINAL_STATUSES` - Statuses that prevent further updates

## Key Implementation Details

### Multilingual Support
**LLM mode:** Native multilingual understanding - the AI model automatically handles English, German, and other languages without explicit configuration.

**Rules mode:** All keywords in `config/keywords.py` include both English and German translations. No language detection is performed - all keywords work simultaneously. This approach is extensible to additional languages.

### OAuth2 Authentication
**Unified authentication** (config/settings.py:36-40) - Single token.json contains combined scopes for both Gmail (read-only) and Google Sheets APIs, reducing authentication friction.

### Gmail Category Filtering
**Primary inbox focus** (gmail/fetcher.py:32) - The Gmail search query excludes promotional and social category emails using `-category:promotions -category:social`. This ensures only primary inbox emails are processed, significantly reducing false positives from marketing emails, job alerts, and social network notifications. Updates and Forums categories are still included as they may contain legitimate job application confirmations.

### File Persistence
**Five persistent files** in project root (all in .gitignore):
- `credentials.json` - OAuth2 credentials from Google Cloud Console
- `token.json` - OAuth2 access/refresh tokens (auto-generated)
- `llm_cache.json` - LLM analysis cache (auto-generated, saves API costs)
- `processed_emails.json` - Tracking file for processed email IDs (auto-generated, use `--reset-tracking` to clear)
- `false_positives.json` - Tracking file for deleted applications (auto-generated, use `--reset-tracking` to clear)

### Gmail Thread Tracking
Thread IDs are preserved in applications to enable perfect matching of follow-up emails in the same conversation thread (matching/matcher.py:54-70).

### Company Name Normalization
`utils/text_utils.py` provides `normalize_company_name()` which strips common suffixes (Inc., LLC, GmbH, etc.) and normalizes whitespace for accurate matching.

## Common Adjustments

### Choosing Analysis Mode
Use `--mode llm` (default) for:
- Higher accuracy (95%+ company names, 90%+ status)
- Better false positive filtering
- Context-aware analysis
- Cost: ~$0.01 per 100 NEW emails (cached emails are free!)

Use `--mode rules` for:
- Offline operation (no API dependency)
- Zero cost
- Faster processing (no API calls)
- Trade-off: Lower accuracy, more false positives

### Managing LLM Cache
**Cache grows over time** as new emails are analyzed. To manage:
- **View cache size**: `ls -lh llm_cache.json`
- **Clear cache** (force re-analysis of all emails): `rm llm_cache.json`
- **Cache location**: Project root directory (`llm_cache.json`)
- **Cache format**: JSON with message_id as key
- Cache is automatically excluded from git (.gitignore)

### Choosing an LLM Provider

**Cost Comparison (per 100 emails):**
- DeepSeek: ~$0.01 (most cost-effective)
- Google Gemini: ~$0.15
- Anthropic Claude: ~$0.25
- OpenAI GPT: ~$0.30

**Quality Comparison:**
All providers achieve >90% accuracy for job email detection. Differences are minimal for this use case.

**Switching Providers:**
```bash
# Change provider in .env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...

# Cache is provider-agnostic - preserved when switching!
uv run python main.py
```

**Backward Compatibility:**
If you have `DEEPSEEK_API_KEY` in `.env` without `LLM_PROVIDER`, DeepSeek is used automatically.

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

**Example use case:**
If you notice application dates showing rejection dates instead of initial application dates:
```bash
# Reset tracking and re-process - confirmation emails will now be detected
uv run python main.py --reset-tracking --days 60
```
This is especially useful after detection keyword updates that improve confirmation email detection.

### Detection Too Strict/Loose (Rules Mode)
Edit `DETECTION_THRESHOLD` in `.env`:
- Lower (3-4): Catch more emails, possible false positives
- Higher (6-7): Stricter detection, may miss some emails
- Or switch to `--mode llm` for better accuracy

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

llm/             # LLM-based analysis (default mode)
├── llm_client.py       # Multi-provider LLM client using LiteLLM
├── prompts.py          # Structured prompt templates with examples
└── email_analyzer.py   # Main LLM analyzer with caching and fallback

detection/       # Rules-based email analysis (--mode rules)
├── detector.py  # Scoring algorithm for job detection
├── classifier.py # Determine email type and status
└── extractor.py # Extract company and position from text

matching/        # Application matching logic (both modes)
└── matcher.py   # 4-strategy matching algorithm

sheets/          # Google Sheets integration (both modes)
├── client.py    # Low-level Sheets API wrapper
└── manager.py   # High-level application CRUD operations

models/          # Data structures (both modes)
├── email.py     # Email data model
└── application.py # Application data model

utils/           # Helper functions (both modes)
└── text_utils.py # Text normalization and keyword matching

main.py          # CLI entry point and orchestration

# Auto-generated files (in .gitignore)
credentials.json      # OAuth2 credentials (manual download from GCP)
token.json            # OAuth2 access tokens (auto-generated on first run)
llm_cache.json        # LLM analysis cache (auto-generated, persistent)
processed_emails.json # Processed message IDs tracker (use --reset-tracking to clear)
false_positives.json  # False positives tracker (use --reset-tracking to clear)
```

## Testing and Debugging

Use `--dry-run` mode extensively when:
- Testing detection threshold changes
- Validating matching behavior
- Previewing what would be updated before committing to spreadsheet
- Comparing LLM vs rules mode: `python main.py --dry-run` vs `python main.py --mode rules --dry-run`

The CLI output shows:
- Analysis mode being used (LLM or Rules)
- Cache load message: "Loaded X cached results from llm_cache.json" (LLM mode)
- Detection scores for understanding why emails matched/didn't match (rules mode)
- LLM reasoning and confidence scores (LLM mode)
- Matching confidence levels for troubleshooting duplicate applications
- Summary statistics for monitoring system performance

**Comparing Modes:**
Run both modes in dry-run to compare accuracy:
```bash
# LLM mode
python main.py --dry-run --days 15

# Rules mode
python main.py --mode rules --dry-run --days 15
```
Compare the sample outputs to see which mode provides better results for your email patterns.
