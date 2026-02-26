"""
MCP Server: Communications
==========================
FastMCP server exposing external-action tools to Claude Code:

  send_email(to, subject, body)          — SMTP via Gmail
  post_to_linkedin(content)              — LinkedIn UGC Posts API
  send_whatsapp_message(to, message)     — WhatsApp Business API (optional)
  log_to_vault(message, log_type)        — Write a log entry to /Logs/

This is the "Hands" layer of the AI Employee.
Every tool call that touches the outside world goes through here.
All sensitive tools log their execution to /Logs/ automatically.

Setup:
  1. Fill in credentials in .env (copy .env.example)
  2. Add this server to .claude/mcp.json (already done)
  3. Run: python mcp_servers/communications.py

Usage:
    python mcp_servers/communications.py          # start MCP server (stdio)
    python mcp_servers/communications.py --test   # run self-test without real sends
"""

import json
import os
import smtplib
import sys
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

try:
    import requests
    from dotenv import load_dotenv
    from fastmcp import FastMCP
except ImportError:
    print("ERROR: Run: pip install fastmcp requests python-dotenv", file=sys.stderr)
    sys.exit(1)

VAULT_ROOT = Path(__file__).parent.parent
load_dotenv(VAULT_ROOT / ".env")

mcp = FastMCP(
    name="ai-employee-communications",
    instructions=(
        "External communications server for the AI Employee. "
        "All tools that touch the outside world. "
        "Only call these tools after a human has approved the action in /Approved/."
    ),
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _datestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _write_log(action: str, details: dict, result: str):
    logs = VAULT_ROOT / "Logs"
    logs.mkdir(exist_ok=True)
    slug = action.replace(".", "_").replace(" ", "_")
    log_file = logs / f"{_datestamp()}_{slug}.md"
    # Append if file exists (multiple actions same day)
    mode = "a" if log_file.exists() else "w"
    with log_file.open(mode, encoding="utf-8") as f:
        f.write(
            f"\n## {action} — {_now()}\n\n"
            f"```json\n{json.dumps(details, indent=2)}\n```\n\n"
            f"**Result:** {result}\n"
        )


# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp.tool()
def send_email(to: str, subject: str, body: str, cc: str = "") -> str:
    """
    Send an email via Gmail SMTP.
    Requires GMAIL_ADDRESS and GMAIL_APP_PASSWORD in .env.
    ONLY call this after the email content has been approved in /Approved/.

    Args:
        to: Recipient email address
        subject: Email subject line
        body: Plain-text email body
        cc: Optional CC address (leave empty if not needed)

    Returns:
        Success message with timestamp, or error description.
    """
    gmail_address = os.getenv("GMAIL_ADDRESS")
    app_password = os.getenv("GMAIL_APP_PASSWORD")
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))

    if not gmail_address or not app_password:
        return "ERROR: GMAIL_ADDRESS and GMAIL_APP_PASSWORD not set in .env"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = gmail_address
    msg["To"] = to
    if cc:
        msg["Cc"] = cc
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(gmail_address, app_password)
            recipients = [to] + ([cc] if cc else [])
            server.sendmail(gmail_address, recipients, msg.as_string())

        details = {"to": to, "subject": subject, "cc": cc, "body_preview": body[:100]}
        _write_log("email_sent", details, "Success")
        return f"Email sent successfully to {to} at {_now()}"

    except Exception as exc:
        _write_log("email_sent", {"to": to, "subject": subject}, f"FAILED: {exc}")
        return f"ERROR sending email: {exc}"


@mcp.tool()
def post_to_linkedin(content: str, visibility: str = "PUBLIC") -> str:
    """
    Publish a post to LinkedIn.
    Requires LINKEDIN_ACCESS_TOKEN and LINKEDIN_AUTHOR_URN in .env.
    ONLY call this after the post has been approved in /Approved/.

    Args:
        content: The full text of the LinkedIn post (150–300 words recommended)
        visibility: "PUBLIC" (default) or "CONNECTIONS"

    Returns:
        Post ID on success, or error description.
    """
    access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    author_urn = os.getenv("LINKEDIN_AUTHOR_URN")

    if not access_token or not author_urn:
        return "ERROR: LINKEDIN_ACCESS_TOKEN and LINKEDIN_AUTHOR_URN not set in .env"

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
            "com.linkedin.ugc.MemberNetworkVisibility": visibility
        },
    }

    try:
        resp = requests.post(
            "https://api.linkedin.com/v2/ugcPosts",
            headers=headers, json=payload, timeout=30
        )
        resp.raise_for_status()
        post_id = resp.json().get("id", "unknown")
        _write_log("linkedin_posted", {"content_preview": content[:120], "post_id": post_id}, "Success")
        return f"LinkedIn post published. Post ID: {post_id}"

    except requests.HTTPError as exc:
        _write_log("linkedin_posted", {"content_preview": content[:120]}, f"FAILED: {exc}")
        return f"ERROR posting to LinkedIn: {exc} — Response: {exc.response.text[:200]}"


@mcp.tool()
def send_whatsapp_message(to: str, message: str) -> str:
    """
    Send a WhatsApp message via the WhatsApp Business Cloud API.
    Requires WHATSAPP_API_TOKEN and WHATSAPP_PHONE_NUMBER_ID in .env.
    ONLY call this after the message has been approved in /Approved/.

    Args:
        to: Recipient phone number in E.164 format (e.g., +447911123456)
        message: The message text to send

    Returns:
        Message ID on success, or error description.
    """
    token = os.getenv("WHATSAPP_API_TOKEN")
    phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

    if not token or not phone_id:
        return "ERROR: WHATSAPP_API_TOKEN and WHATSAPP_PHONE_NUMBER_ID not set in .env"

    url = f"https://graph.facebook.com/v19.0/{phone_id}/messages"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message},
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        msg_id = resp.json().get("messages", [{}])[0].get("id", "unknown")
        _write_log("whatsapp_sent", {"to": to, "message_preview": message[:80]}, "Success")
        return f"WhatsApp message sent to {to}. Message ID: {msg_id}"

    except requests.HTTPError as exc:
        _write_log("whatsapp_sent", {"to": to}, f"FAILED: {exc}")
        return f"ERROR sending WhatsApp: {exc}"


@mcp.tool()
def log_to_vault(message: str, log_type: str = "info") -> str:
    """
    Write a log entry to /Logs/ in the vault.
    Use this to record any significant event that doesn't have its own log.

    Args:
        message: The log message (plain text or markdown)
        log_type: One of: info, warning, error, action

    Returns:
        Path of the log file written.
    """
    _write_log(f"mcp_{log_type}", {"message": message}, "Logged")
    return f"Logged to /Logs/ at {_now()}"


# ── Entry point ───────────────────────────────────────────────────────────────

def _self_test():
    print("=== MCP Communications Server - Self Test ===\n")
    print("Tools registered:")
    for tool in [send_email, post_to_linkedin, send_whatsapp_message, log_to_vault]:
        print(f"  [OK] {tool.__name__}")

    print("\nTesting log_to_vault (safe — no external calls)...")
    result = log_to_vault("Self-test: MCP communications server started", "info")
    print(f"  Result: {result}")

    env_checks = {
        "GMAIL_ADDRESS": bool(os.getenv("GMAIL_ADDRESS")),
        "GMAIL_APP_PASSWORD": bool(os.getenv("GMAIL_APP_PASSWORD")),
        "LINKEDIN_ACCESS_TOKEN": bool(os.getenv("LINKEDIN_ACCESS_TOKEN")),
        "LINKEDIN_AUTHOR_URN": bool(os.getenv("LINKEDIN_AUTHOR_URN")),
    }
    print("\nCredentials in .env:")
    for key, present in env_checks.items():
        status = "[SET]" if present else "[NOT SET] - add to .env"
        print(f"  {key}: {status}")

    print("\n[OK] Server ready. Run without --test to start in stdio MCP mode.")


def main():
    if "--test" in sys.argv:
        _self_test()
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
