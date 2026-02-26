"""
Sentinel: WhatsApp Watcher (Playwright / WhatsApp Web)
=======================================================
Automates WhatsApp Web via Playwright to detect unread messages containing
keywords and drop task files into /Needs_Action for Claude to respond to.

NOTE: This uses browser automation of WhatsApp Web. Review WhatsApp's Terms
      of Service before deploying in a production environment.

Extends BaseWatcher -- implements check_for_updates() and create_action_file().

How it works:
  1. Launches a persistent Chromium profile (session survives across runs)
  2. Loads https://web.whatsapp.com using the saved session (no QR scan after setup)
  3. Scans the chat list for unread conversations
  4. Filters by keyword: 'urgent', 'asap', 'invoice', 'payment', 'help'
  5. Extracts sender + message text BEFORE closing the browser
  6. Writes /Needs_Action task files for Claude to draft replies

IMPORTANT - First-time setup:
  Run with --setup once to scan the QR code and save the browser session:
      python sentinels/whatsapp_watcher.py --setup
  After that, all subsequent runs are headless.

Setup:
  1. Install Playwright: pip install playwright && playwright install chromium
  2. Run: python sentinels/whatsapp_watcher.py --setup
     (browser opens, scan QR code with your phone, session saves automatically)
  3. Set in .env: WHATSAPP_SESSION_PATH=.claude/whatsapp_session

Usage:
    python sentinels/whatsapp_watcher.py           # run once (headless)
    python sentinels/whatsapp_watcher.py --setup   # first-time QR scan
    python sentinels/whatsapp_watcher.py --loop    # poll every 30 seconds
"""

import json
import os
import sys
from pathlib import Path

VAULT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))
from base_watcher import BaseWatcher

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("ERROR: Run: pip install playwright && playwright install chromium")
    sys.exit(1)

POLL_INTERVAL = 30   # seconds


class WhatsAppWatcher(BaseWatcher):
    """
    Monitors WhatsApp Web for unread messages matching business keywords.
    Writes /Needs_Action task files for Claude to draft replies.

    All Playwright element data is extracted INSIDE the browser context
    before close() is called — only serializable dicts leave the browser.
    """

    def __init__(self, vault_path=None, session_path=None):
        super().__init__(vault_path or VAULT_ROOT, check_interval=POLL_INTERVAL)
        self.session_path = Path(
            session_path
            or os.getenv("WHATSAPP_SESSION_PATH", str(self.vault_path / ".claude" / "whatsapp_session"))
        )
        self.keywords = ["urgent", "asap", "invoice", "payment", "help", "problem", "issue"]

    # ── BaseWatcher contract ──────────────────────────────────────────────────

    def check_for_updates(self) -> list:
        """
        Launch headless Chromium, load WhatsApp Web, extract unread keyword
        messages, close browser, return serializable list of message dicts.

        Returns [] if session not found or WhatsApp Web times out.
        """
        if not self.session_path.exists():
            self.logger.info(
                f"WhatsApp session not found at {self.session_path} -- skipping.\n"
                f"  Run: python sentinels/whatsapp_watcher.py --setup"
            )
            return []

        self.logger.info("Checking WhatsApp Web for new messages...")
        try:
            return self._scrape_messages(headless=True)
        except PlaywrightTimeout:
            self.logger.error(
                "WhatsApp Web timed out (graceful degradation). "
                "Session may have expired -- run --setup again."
            )
            return []
        except Exception as exc:
            self.logger.error(f"WhatsApp error (graceful degradation): {exc}")
            return []

    def create_action_file(self, message: dict) -> Path:
        """
        Write a /Needs_Action task file for one WhatsApp message.
        message is a plain dict -- no Playwright elements.
        """
        sender_slug = message["sender"].lower().replace(" ", "-")[:30]
        filename = f"{self.datestamp()}_whatsapp_{sender_slug}.md"
        filepath = self.needs_action / filename

        keywords_found = ", ".join(message.get("keywords_matched", [])) or "keyword match"

        content = (
            f"---\n"
            f"type: whatsapp\n"
            f"from: {message['sender']}\n"
            f"received: {self.now()}\n"
            f"keywords: {keywords_found}\n"
            f"priority: high\n"
            f"status: pending\n"
            f"---\n\n"
            f"# WhatsApp: Message from {message['sender']}\n\n"
            f"**From:** {message['sender']}\n"
            f"**Keywords detected:** {keywords_found}\n"
            f"**Received:** {self.now()}\n\n"
            f"---\n\n"
            f"## Message Content\n\n"
            f"{message['text']}\n\n"
            f"---\n\n"
            f"## Rules of Engagement\n\n"
            f"- Always be polite on WhatsApp (see `Company_Handbook.md`)\n"
            f"- Do NOT send any reply without human approval\n"
            f"- If message contains a payment request > $500, flag immediately\n\n"
            f"## Suggested Actions\n\n"
            f"- [ ] Reply to sender\n"
            f"- [ ] Forward to relevant party\n"
            f"- [ ] Archive after processing\n\n"
            f"## What Claude Should Do\n\n"
            f"1. Read and understand the message intent\n"
            f"2. Draft a warm, professional reply using tone from `Company_Handbook.md`\n"
            f"3. Save draft to `/Pending_Approval/` with `> Type: whatsapp_reply`\n"
            f"4. Move this task to `/Done` after approval decision\n"
        )

        self.needs_action.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content, encoding="utf-8")

        self.log_event(
            "whatsapp.inbound",
            {
                "sender": message["sender"],
                "keywords": message.get("keywords_matched", []),
                "task_file": filename,
                "preview": message["text"][:120],
            },
        )
        self.logger.info(
            f"WHATSAPP: '{keywords_found}' from {message['sender']} >> {filename}"
        )
        return filepath

    # ── Private: browser automation ───────────────────────────────────────────

    def _scrape_messages(self, headless: bool) -> list:
        """
        Open WhatsApp Web, find unread keyword chats, extract all data,
        close browser. Returns list of plain dicts (no Playwright elements).
        """
        messages = []

        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                str(self.session_path),
                headless=headless,
                args=["--no-sandbox"],
            )

            # Use existing page or open a new one
            page = browser.pages[0] if browser.pages else browser.new_page()
            page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")

            # Wait for the chat list to confirm session is valid
            try:
                page.wait_for_selector('[data-testid="chat-list"]', timeout=20_000)
            except PlaywrightTimeout:
                browser.close()
                raise PlaywrightTimeout("Chat list not found — session may need renewal")

            # Small settle delay for unread badges to render
            page.wait_for_timeout(2000)

            # Find all chat rows with an unread count badge
            unread_chats = page.query_selector_all('[data-testid="cell-frame-container"]')

            for chat in unread_chats:
                # Check for unread count badge inside this chat row
                badge = chat.query_selector('[data-testid="icon-unread-count"]')
                if not badge:
                    # Fallback: look for any element with 'unread' in aria-label
                    badge = chat.query_selector('[aria-label*="unread"]')
                if not badge:
                    continue

                # Extract sender name
                title_el = chat.query_selector('[data-testid="cell-frame-title"]')
                sender = title_el.inner_text().strip() if title_el else "Unknown"

                # Extract last message preview
                subtitle_el = chat.query_selector('[data-testid="last-msg-status"] + span')
                if not subtitle_el:
                    subtitle_el = chat.query_selector('[data-testid="cell-frame-secondary-detail"]')
                text = subtitle_el.inner_text().strip() if subtitle_el else chat.inner_text().strip()

                # Keyword filter
                text_lower = text.lower()
                matched = [kw for kw in self.keywords if kw in text_lower]
                if not matched:
                    continue

                # All data extracted as plain Python -- safe after browser.close()
                messages.append({
                    "sender": sender,
                    "text": text,
                    "keywords_matched": matched,
                })

            browser.close()

        self.logger.info(f"WhatsApp: scanned chats, {len(messages)} keyword match(es) found.")
        return messages

    # ── Setup mode (first-time QR scan) ──────────────────────────────────────

    def setup_session(self):
        """
        Run with headless=False so user can scan the QR code.
        Session is saved to self.session_path for future headless runs.
        Timeout extended to 5 minutes to give enough time to scan.
        """
        print(f"\n[WhatsApp Setup] Opening browser — scan the QR code with your phone.")
        print(f"Session will be saved to: {self.session_path}")
        print(f"You have 5 minutes to scan the QR code.\n")
        self.session_path.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                str(self.session_path),
                headless=False,
            )
            page = browser.pages[0] if browser.pages else browser.new_page()
            page.goto("https://web.whatsapp.com")
            print("Browser open — scan the QR code now with your phone...")
            print("(WhatsApp > Linked Devices > Link a Device)\n")

            try:
                page.wait_for_selector('[data-testid="chat-list"]', timeout=300_000)
                print("\n[OK] WhatsApp session saved successfully.")
                print(f"Session stored at: {self.session_path}")
                print(f"\nNext step: set in .env:")
                print(f"  WHATSAPP_SESSION_PATH={self.session_path}")
                print(f"\nThen run: python sentinels/whatsapp_watcher.py")
            except PlaywrightTimeout:
                print("\n[TIMEOUT] QR code was not scanned within 5 minutes. Try again.")
            except Exception as exc:
                print(f"\n[INFO] Browser closed early: {exc}")
                print("If you closed the browser after scanning, the session may still be saved.")
                print(f"Test with: python sentinels/whatsapp_watcher.py")
            finally:
                try:
                    browser.close()
                except Exception:
                    pass  # browser already closed — session still saved to disk


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="WhatsApp watcher (Playwright / WhatsApp Web)")
    parser.add_argument("--setup", action="store_true", help="First-time QR scan (opens browser)")
    parser.add_argument("--loop", action="store_true", help=f"Poll every {POLL_INTERVAL}s (headless)")
    parser.add_argument("--session", default=None, help="Override session path")
    args = parser.parse_args()

    watcher = WhatsAppWatcher(session_path=args.session)

    if args.setup:
        watcher.setup_session()
    elif args.loop:
        print(f"[WhatsApp Sentinel] Polling every {POLL_INTERVAL}s. Ctrl+C to stop.\n")
        watcher.run()
    else:
        items = watcher.run_once()
        if not items:
            print(f"[{watcher.now()}] No new keyword messages.")
        else:
            print(f"[{watcher.now()}] {len(items)} message(s) written to /Needs_Action.")


if __name__ == "__main__":
    main()
