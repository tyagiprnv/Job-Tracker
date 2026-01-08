"""Google Sheets OAuth2 authentication."""

import gspread
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from config.settings import ALL_SCOPES, CREDENTIALS_FILE, GMAIL_TOKEN_FILE


def get_sheets_client():
    """Get authenticated Google Sheets client using gspread.

    Returns:
        gspread.Client: Authenticated gspread client

    Raises:
        FileNotFoundError: If credentials.json is missing
        Exception: If authentication fails
    """
    creds = None

    # Use the same token file as Gmail (both use same OAuth client)
    if GMAIL_TOKEN_FILE.exists():
        # Load existing credentials
        creds = Credentials.from_authorized_user_file(
            str(GMAIL_TOKEN_FILE), ALL_SCOPES
        )

    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Refresh expired token
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing token: {e}")
                print("Re-authenticating...")
                creds = None

        if not creds:
            # Perform OAuth2 flow
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    f"credentials.json not found at {CREDENTIALS_FILE}.\n"
                    "Please download OAuth2 credentials from Google Cloud Console:\n"
                    "1. Go to https://console.cloud.google.com/\n"
                    "2. Enable Gmail API and Google Sheets API\n"
                    "3. Create OAuth2 credentials (Desktop app)\n"
                    "4. Download and save as credentials.json in project root"
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), ALL_SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save credentials for next run
        with open(GMAIL_TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    # Create gspread client
    client = gspread.authorize(creds)
    return client


def test_sheets_connection(spreadsheet_id: str):
    """Test Google Sheets API connection.

    Args:
        spreadsheet_id: ID of spreadsheet to test

    Returns:
        bool: True if connection successful
    """
    try:
        client = get_sheets_client()
        # Try to open spreadsheet
        spreadsheet = client.open_by_key(spreadsheet_id)
        print(f"Successfully connected to Google Sheets: {spreadsheet.title}")
        return True
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"Spreadsheet not found with ID: {spreadsheet_id}")
        print("Please check the SPREADSHEET_ID in your .env file")
        return False
    except Exception as e:
        print(f"Error connecting to Google Sheets: {e}")
        return False
