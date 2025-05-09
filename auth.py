# auth_google.py  – run once to create a multi-scope token
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",     # Gmail
    "https://www.googleapis.com/auth/calendar.readonly",  # Calendar
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.insert",  # for uploading .eml files
    # add more (e.g. .auth/gmail.modify or .auth/calendar) if you need write access
]

token_path = Path("token.json")
creds = None

if token_path.exists():
    creds = Credentials.from_authorized_user_file(token_path, SCOPES)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json", SCOPES
        )
        creds = flow.run_local_server(port=0)

    token_path.write_text(creds.to_json())

print("✅ unified token.json created with Gmail + Calendar scopes!")
