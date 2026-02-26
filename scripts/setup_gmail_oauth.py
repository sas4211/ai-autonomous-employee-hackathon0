"""
Gmail OAuth2 Setup — Run Once
==============================
Runs the browser-based OAuth2 flow to generate gmail_token.json.
After this, gmail_watcher.py can authenticate without a browser.

Steps:
  1. Go to Google Cloud Console: https://console.cloud.google.com/
  2. Create a project (or select existing)
  3. Enable Gmail API: APIs & Services > Library > Gmail API > Enable
  4. Create OAuth credentials:
       APIs & Services > Credentials > Create Credentials > OAuth client ID
       Application type: Desktop app
       Download as: credentials.json
  5. Place credentials.json in this project's root or set GMAIL_OAUTH_CLIENT_FILE
  6. Run this script:
       python scripts/setup_gmail_oauth.py
  7. Sign in with your Google account in the browser that opens
  8. Token is saved to .claude/gmail_token.json

Usage:
    python scripts/setup_gmail_oauth.py
    python scripts/setup_gmail_oauth.py --client-file path/to/credentials.json
    python scripts/setup_gmail_oauth.py --token-out path/to/gmail_token.json
"""

import argparse
import sys
from pathlib import Path

VAULT_ROOT = Path(__file__).parent.parent

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
except ImportError:
    print("ERROR: Run: pip install google-auth-oauthlib google-auth google-api-python-client")
    sys.exit(1)

# Scopes required by gmail_watcher.py:
#   readonly = read messages
#   modify   = mark as read (optional, but allows future use)
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]


def run_oauth_flow(client_file: str, token_out: str):
    token_path = Path(token_out)
    client_path = Path(client_file)

    if not client_path.exists():
        print(f"ERROR: OAuth client file not found: {client_path}")
        print("  Download it from Google Cloud Console:")
        print("  APIs & Services > Credentials > OAuth 2.0 Client IDs > Download JSON")
        sys.exit(1)

    creds = None

    # Reuse existing token if valid
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Token expired — refreshing automatically...")
            creds.refresh(Request())
        else:
            print("Opening browser for Google sign-in...")
            flow = InstalledAppFlow.from_client_secrets_file(str(client_path), SCOPES)
            creds = flow.run_local_server(port=0)

    # Save token
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json(), encoding="utf-8")
    print(f"\n[OK] Token saved to: {token_path}")
    print(f"\nNext step: set in .env:")
    print(f"  GMAIL_CREDENTIALS_PATH={token_path}")
    print(f"\nThen run: python sentinels/gmail_watcher.py")


def main():
    parser = argparse.ArgumentParser(description="Gmail OAuth2 setup (run once)")
    parser.add_argument(
        "--client-file",
        default=str(VAULT_ROOT / "credentials.json"),
        help="Path to OAuth client credentials JSON (from Google Cloud Console)",
    )
    parser.add_argument(
        "--token-out",
        default=str(VAULT_ROOT / ".claude" / "gmail_token.json"),
        help="Where to save the generated token (default: .claude/gmail_token.json)",
    )
    args = parser.parse_args()

    print("=== Gmail OAuth2 Setup ===")
    print(f"Client file : {args.client_file}")
    print(f"Token output: {args.token_out}\n")

    run_oauth_flow(args.client_file, args.token_out)


if __name__ == "__main__":
    main()
