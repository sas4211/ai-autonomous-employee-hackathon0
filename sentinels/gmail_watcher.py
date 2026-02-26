"""
Sentinel: Gmail Watcher
=======================
Polls Gmail API (OAuth2) for unread+important emails and drops task files
into /Needs_Action for Claude to respond to.

Extends BaseWatcher -- implements check_for_updates() and create_action_file().

Uses Gmail API v1 (not IMAP) for label filtering, structured metadata,
and reliable OAuth2 auth. Filters: is:unread is:important.

Setup (one-time):
  1. Enable Gmail API in Google Cloud Console:
     https://console.cloud.google.com/apis/library/gmail.googleapis.com
  2. Create OAuth2 Desktop credentials -> download as credentials.json
  3. Run the auth flow:
        python scripts/setup_gmail_oauth.py
     This opens a browser, asks you to sign in, and saves gmail_token.json.
  4. Set in .env:
        GMAIL_CREDENTIALS_PATH=.claude/gmail_token.json

Usage:
    python sentinels/gmail_watcher.py          # run once
    python sentinels/gmail_watcher.py --loop   # poll every 2 minutes
"""

import json
import os
import sys
import base64
from datetime import datetime, timezone
from pathlib import Path

VAULT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))
from base_watcher import BaseWatcher

try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("ERROR: Run: pip install google-auth google-auth-oauthlib google-api-python-client")
    sys.exit(1)

POLL_INTERVAL = 120   # 2 minutes
STATE_FILE = VAULT_ROOT / ".claude" / "gmail_processed_ids.json"
MAX_PROCESSED_IDS = 2000   # cap state file size


# ── State persistence ─────────────────────────────────────────────────────────

def _load_processed_ids() -> set:
    if STATE_FILE.exists():
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return set(data.get("ids", []))
    return set()


def _save_processed_ids(ids: set):
    STATE_FILE.parent.mkdir(exist_ok=True)
    # Keep only the most recent MAX_PROCESSED_IDS to prevent unbounded growth
    trimmed = list(ids)[-MAX_PROCESSED_IDS:]
    STATE_FILE.write_text(
        json.dumps({"ids": trimmed}, indent=2), encoding="utf-8"
    )


# ── Body extraction ───────────────────────────────────────────────────────────

def _extract_body(payload: dict) -> str:
    """Recursively extract plain-text body from Gmail API message payload."""
    mime_type = payload.get("mimeType", "")

    if mime_type == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")

    # Multipart: walk parts recursively
    for part in payload.get("parts", []):
        result = _extract_body(part)
        if result:
            return result

    # Fallback: nothing extractable
    return ""


# ── Watcher class ─────────────────────────────────────────────────────────────

class GmailWatcher(BaseWatcher):
    """
    Polls Gmail API for unread+important emails and creates
    /Needs_Action task files with YAML frontmatter for Claude to respond to.
    """

    def __init__(self, vault_path=None, credentials_path=None):
        super().__init__(vault_path or VAULT_ROOT, check_interval=POLL_INTERVAL)
        self.credentials_path = credentials_path or os.getenv(
            "GMAIL_CREDENTIALS_PATH",
            str(self.vault_path / ".claude" / "gmail_token.json"),
        )
        self.service = None           # initialized lazily on first check
        self.processed_ids = _load_processed_ids()

    # ── BaseWatcher contract ──────────────────────────────────────────────────

    def check_for_updates(self) -> list:
        """
        Return list of unread+important Gmail message dicts.
        Returns [] if credentials are missing or Gmail API is unreachable.
        """
        if not Path(self.credentials_path).exists():
            self.logger.info(
                f"Gmail credentials not found at {self.credentials_path} -- skipping.\n"
                f"  Run: python scripts/setup_gmail_oauth.py"
            )
            return []

        try:
            service = self._get_service()
            results = (
                service.users()
                .messages()
                .list(userId="me", q="is:unread is:important")
                .execute()
            )
            messages = results.get("messages", [])
            new = [m for m in messages if m["id"] not in self.processed_ids]
            self.logger.info(
                f"Gmail: {len(messages)} unread+important, {len(new)} new to process."
            )
            return new

        except HttpError as exc:
            self.logger.error(f"Gmail API error (graceful degradation): {exc}")
            return []
        except Exception as exc:
            self.logger.error(f"Gmail unexpected error (graceful degradation): {exc}")
            return []

    def create_action_file(self, message: dict) -> Path:
        """
        Fetch full message, extract headers + body, write /Needs_Action task file
        with YAML frontmatter. Marks message ID as processed.
        """
        try:
            service = self._get_service()
            msg = (
                service.users()
                .messages()
                .get(userId="me", id=message["id"], format="full")
                .execute()
            )
        except HttpError as exc:
            self.logger.error(f"Failed to fetch message {message['id']}: {exc}")
            return None

        # Extract headers
        headers = {
            h["name"]: h["value"]
            for h in msg.get("payload", {}).get("headers", [])
        }
        sender = headers.get("From", "Unknown")
        subject = headers.get("Subject", "No Subject")
        date_header = headers.get("Date", self.now())

        # Extract body (prefer full text, fallback to snippet)
        body = _extract_body(msg.get("payload", {})).strip()
        if not body:
            body = msg.get("snippet", "(no body)")

        # Truncate very long emails
        if len(body) > 3000:
            body = body[:3000] + "\n\n[... truncated — see Gmail for full message]"

        # Write task file with YAML frontmatter
        filepath = self.needs_action / f"EMAIL_{message['id']}.md"
        content = (
            f"---\n"
            f"type: email\n"
            f"from: {sender}\n"
            f"subject: {subject}\n"
            f"received: {datetime.now(timezone.utc).isoformat()}\n"
            f"date_sent: {date_header}\n"
            f"gmail_id: {message['id']}\n"
            f"priority: high\n"
            f"status: pending\n"
            f"---\n\n"
            f"# Email: {subject}\n\n"
            f"**From:** {sender}\n"
            f"**Received:** {date_header}\n\n"
            f"---\n\n"
            f"## Email Content\n\n"
            f"{body}\n\n"
            f"---\n\n"
            f"## Rules of Engagement\n\n"
            f"- Always reply politely and professionally (see `Company_Handbook.md`)\n"
            f"- Do NOT send any reply without human approval\n"
            f"- If the email contains a payment request > $500, flag to /Needs_Action\n\n"
            f"## Suggested Actions\n\n"
            f"- [ ] Reply to sender\n"
            f"- [ ] Forward to relevant party\n"
            f"- [ ] Archive after processing\n\n"
            f"## What Claude Should Do\n\n"
            f"1. Read and understand the email\n"
            f"2. Load skill: `skills/gmail_send.skill.md`\n"
            f"3. Draft a reply using tone from `Company_Handbook.md`\n"
            f"4. Save draft to `/Pending_Approval/` — do NOT send directly\n"
            f"5. Move this task to `/Done` after approval decision\n"
        )

        self.needs_action.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content, encoding="utf-8")

        # Persist processed state
        self.processed_ids.add(message["id"])
        _save_processed_ids(self.processed_ids)

        self.log_event(
            "email.inbound",
            {
                "gmail_id": message["id"],
                "task_file": filepath.name,
                "from": sender,
                "subject": subject,
            },
        )
        self.logger.info(f"NEW EMAIL >> {filepath.name} | From: {sender} | {subject}")
        return filepath

    # ── Private helpers ───────────────────────────────────────────────────────

    def _get_service(self):
        """Lazily initialise and cache the Gmail API service."""
        if self.service is None:
            creds = Credentials.from_authorized_user_file(self.credentials_path)
            self.service = build("gmail", "v1", credentials=creds)
        return self.service


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Gmail watcher (Gmail API v1)")
    parser.add_argument("--loop", action="store_true", help=f"Poll every {POLL_INTERVAL}s")
    parser.add_argument(
        "--credentials",
        default=None,
        help="Path to gmail_token.json (default: from GMAIL_CREDENTIALS_PATH env var)",
    )
    args = parser.parse_args()

    watcher = GmailWatcher(credentials_path=args.credentials)

    if args.loop:
        print(f"[Gmail Sentinel] Polling every {POLL_INTERVAL}s. Ctrl+C to stop.\n")
        watcher.run()
    else:
        items = watcher.run_once()
        if not items:
            print(f"[{watcher.now()}] No new important emails.")
        else:
            print(f"[{watcher.now()}] {len(items)} email(s) written to /Needs_Action.")


if __name__ == "__main__":
    main()
