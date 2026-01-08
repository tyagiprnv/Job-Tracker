"""Gmail OAuth2 authentication."""

import os
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config.settings import ALL_SCOPES, CREDENTIALS_FILE, GMAIL_TOKEN_FILE


def get_gmail_service():
    """Get authenticated Gmail API service.

    Returns:
        Gmail API service object

    Raises:
        FileNotFoundError: If credentials.json is missing
        Exception: If authentication fails
    """
    creds = None

    # Check if token file exists
    if GMAIL_TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(GMAIL_TOKEN_FILE), ALL_SCOPES)

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

    # Build and return service
    service = build("gmail", "v1", credentials=creds)
    return service


def test_gmail_connection():
    """Test Gmail API connection.

    Returns:
        bool: True if connection successful
    """
    try:
        service = get_gmail_service()
        # Try to get user profile
        profile = service.users().getProfile(userId="me").execute()
        print(f"Successfully connected to Gmail: {profile.get('emailAddress')}")
        return True
    except Exception as e:
        print(f"Error connecting to Gmail: {e}")
        return False
