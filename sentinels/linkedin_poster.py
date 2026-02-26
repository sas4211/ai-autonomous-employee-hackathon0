"""
Sentinel: LinkedIn Poster
=========================
Two modes:

  1. WATCH mode  — scans /Approved for LinkedIn post files and publishes them.
  2. DRAFT mode  — drops a "write a LinkedIn post" task into /Inbox so Claude
                   generates content, which then flows through the approval gate.

The typical flow:
  Scheduled trigger → /Inbox task → Claude drafts post → /Pending_Approval →
  Human approves → /Approved → this script publishes → /Done

Setup:
  1. Create a LinkedIn app: https://developer.linkedin.com/
  2. Request scopes: r_liteprofile, w_member_social
  3. Complete OAuth flow to get an access token
  4. Set LINKEDIN_ACCESS_TOKEN and LINKEDIN_AUTHOR_URN in .env

Usage:
    python sentinels/linkedin_poster.py --watch   # publish approved posts
    python sentinels/linkedin_poster.py --draft   # queue a new post for Claude
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
    from dotenv import load_dotenv
except ImportError:
    print("ERROR: Run: pip install requests python-dotenv")
    sys.exit(1)

VAULT_ROOT = Path(__file__).parent.parent
INBOX = VAULT_ROOT / "Inbox"
APPROVED = VAULT_ROOT / "Approved"
DONE = VAULT_ROOT / "Done"
LOGS = VAULT_ROOT / "Logs"
LOGS_EVENTS = LOGS / "events"

LINKEDIN_API = "https://api.linkedin.com/v2/ugcPosts"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _datestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ── LinkedIn API ──────────────────────────────────────────────────────────────

def post_to_linkedin(content: str, access_token: str, author_urn: str) -> dict:
    """Publish a text post to LinkedIn using the UGC Posts API."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    payload = {
        "author": author_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": content},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        },
    }
    resp = requests.post(LINKEDIN_API, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


# ── Vault helpers ─────────────────────────────────────────────────────────────

def _extract_post_content(file_path: Path) -> str | None:
    """Extract the post content block from an approved LinkedIn post file."""
    text = file_path.read_text(encoding="utf-8")
    # Look for a ## LinkedIn Post Content section
    marker = "## LinkedIn Post Content"
    if marker in text:
        start = text.index(marker) + len(marker)
        section = text[start:].strip()
        # Take everything up to the next ## heading
        end = section.find("\n## ")
        return section[:end].strip() if end != -1 else section.strip()
    return None


def _is_linkedin_post(file_path: Path) -> bool:
    text = file_path.read_text(encoding="utf-8")
    return "Type: linkedin_post" in text or "type: linkedin_post" in text.lower()


def _log_event(event_type: str, payload: dict):
    LOGS_EVENTS.mkdir(parents=True, exist_ok=True)
    slug = payload.get("task_file", "unknown").replace(".md", "")
    event = {
        "event_id": str(int(time.time())),
        "event_type": event_type,
        "timestamp": _now(),
        "source": "linkedin_poster",
        "vault": "ai-employee",
        "payload": payload,
    }
    out = LOGS_EVENTS / f"{_datestamp()}_{event_type.replace('.', '_')}_{slug[:30]}.json"
    out.write_text(json.dumps(event, indent=2), encoding="utf-8")


def _write_completion_log(task_name: str, post_id: str, content_preview: str):
    LOGS.mkdir(parents=True, exist_ok=True)
    log_file = LOGS / f"{_datestamp()}_linkedin_posted_{task_name[:40]}.md"
    log_file.write_text(
        f"# Log: LinkedIn Post Published\n\n"
        f"- **Timestamp**: {_now()}\n"
        f"- **Task**: {task_name}\n"
        f"- **Post ID**: {post_id}\n"
        f"- **Content Preview**: {content_preview[:120]}...\n"
        f"- **Result**: Success\n",
        encoding="utf-8",
    )


# ── Modes ─────────────────────────────────────────────────────────────────────

def watch_and_publish():
    """Scan /Approved for LinkedIn post files and publish them."""
    load_dotenv(VAULT_ROOT / ".env")
    access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    author_urn = os.getenv("LINKEDIN_AUTHOR_URN")

    if not access_token or not author_urn:
        print("LinkedIn not configured -- skipping (set LINKEDIN_ACCESS_TOKEN + LINKEDIN_AUTHOR_URN in .env)")
        return

    APPROVED.mkdir(parents=True, exist_ok=True)
    posts = [f for f in APPROVED.iterdir() if f.suffix == ".md" and _is_linkedin_post(f)]

    if not posts:
        print(f"[{_now()}] No approved LinkedIn posts found.")
        return

    for post_file in posts:
        print(f"[{_now()}] Publishing: {post_file.name}")
        content = _extract_post_content(post_file)

        if not content:
            print(f"  SKIP: No '## LinkedIn Post Content' section found in {post_file.name}")
            continue

        try:
            result = post_to_linkedin(content, access_token, author_urn)
            post_id = result.get("id", "unknown")
            print(f"  ✓ Published. Post ID: {post_id}")

            # Move to Done
            done_path = DONE / post_file.name
            DONE.mkdir(parents=True, exist_ok=True)
            post_file.rename(done_path)

            _write_completion_log(post_file.name, post_id, content)
            _log_event("linkedin.published", {"task_file": post_file.name, "post_id": post_id})

        except requests.HTTPError as exc:
            print(f"  ERROR publishing {post_file.name}: {exc}")
            _log_event("linkedin.error", {"task_file": post_file.name, "error": str(exc)})


def queue_draft_task(topic: str = ""):
    """Drop a 'write a LinkedIn post' task into /Inbox for Claude to handle."""
    INBOX.mkdir(parents=True, exist_ok=True)
    date = _datestamp()
    filename = f"{date}_write-linkedin-post.md"
    task_path = INBOX / filename

    topic_line = f"Topic hint: {topic}" if topic else "Topic hint: Share a recent win, insight, or value for your audience."

    task_path.write_text(
        f"# Task: Write LinkedIn Post for Business\n\n"
        f"> Status: **New**\n"
        f"> Created: {date}\n"
        f"> Priority: Medium\n"
        f"> Owner: --\n"
        f"> Type: linkedin_post\n\n"
        f"---\n\n"
        f"## Description\n\n"
        f"Generate a LinkedIn post to promote the business and generate leads.\n"
        f"{topic_line}\n\n"
        f"Use the tone and guidelines in `Company_Handbook.md`.\n\n"
        f"## Post Requirements\n\n"
        f"- 150–300 words\n"
        f"- Hook in the first line (no 'I am excited to announce')\n"
        f"- Clear value for the reader\n"
        f"- One soft call to action (comment, DM, visit link)\n"
        f"- 3–5 relevant hashtags at the end\n\n"
        f"## Output Format\n\n"
        f"Save the approval request to `/Pending_Approval/` with this section:\n\n"
        f"```\n## LinkedIn Post Content\n<post text here>\n```\n\n"
        f"## Acceptance Criteria\n\n"
        f"- [ ] Post drafted and saved to `/Pending_Approval/`\n"
        f"- [ ] Post follows tone guidelines from Company_Handbook.md\n"
        f"- [ ] Type: linkedin_post tag included in the file\n",
        encoding="utf-8",
    )
    print(f"[{_now()}] Queued LinkedIn post task → {filename}")
    _log_event("linkedin.draft_queued", {"task_file": filename})


def main():
    parser = argparse.ArgumentParser(description="LinkedIn poster sentinel")
    parser.add_argument("--watch", action="store_true", help="Publish approved posts")
    parser.add_argument("--draft", action="store_true", help="Queue a new post for Claude")
    parser.add_argument("--topic", default="", help="Topic hint for the draft")
    parser.add_argument("--loop", action="store_true", help="Run --watch on a 10-minute loop")
    args = parser.parse_args()

    if args.draft:
        queue_draft_task(args.topic)
    elif args.loop:
        print("[LinkedIn Sentinel] Watching /Approved every 10 minutes. Ctrl+C to stop.\n")
        while True:
            try:
                watch_and_publish()
            except Exception as exc:
                print(f"[{_now()}] ERROR: {exc}")
            time.sleep(600)
    else:
        watch_and_publish()


if __name__ == "__main__":
    main()
