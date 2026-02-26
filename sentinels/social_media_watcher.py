"""
Sentinel: Social Media Watcher
================================
Monitors Facebook and Twitter/X for inbound signals:
  - Unanswered comments on Facebook page posts
  - Twitter/X @mentions requiring a response

Drops task files into /Inbox for Claude to draft responses.
Extends BaseWatcher -- implements check_for_updates() and create_action_file().

Usage:
    python sentinels/social_media_watcher.py           # run once
    python sentinels/social_media_watcher.py --loop    # poll every 15 minutes
"""

import json
import os
import sys
from pathlib import Path

VAULT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))
from base_watcher import BaseWatcher

try:
    import requests
except ImportError:
    print("ERROR: Run: pip install requests")
    sys.exit(1)

POLL_INTERVAL = 900  # 15 minutes
GRAPH_API = "https://graph.facebook.com/v19.0"
STATE_FILE = VAULT_ROOT / ".claude" / "social_watcher_state.json"


# ── State helpers ─────────────────────────────────────────────────────────────

def _load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"last_fb_comment_time": None, "last_twitter_mention_id": None}


def _save_state(state: dict):
    STATE_FILE.parent.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


# ── Watcher class ─────────────────────────────────────────────────────────────

class SocialMediaWatcher(BaseWatcher):
    """
    Polls Facebook (new comments) and Twitter/X (@mentions).
    Returns mixed list of items with 'platform' field for routing.
    """

    def __init__(self):
        super().__init__(VAULT_ROOT, check_interval=POLL_INTERVAL)
        self.fb_token = os.getenv("FACEBOOK_ACCESS_TOKEN")
        self.fb_page_id = os.getenv("FACEBOOK_PAGE_ID")
        self.tw_bearer = os.getenv("TWITTER_BEARER_TOKEN")
        self.tw_access = os.getenv("TWITTER_ACCESS_TOKEN")

    def check_for_updates(self) -> list:
        """Return list of social media event dicts. Returns [] if none configured."""
        state = _load_state()
        items = []

        if self.fb_token and self.fb_page_id:
            fb_items, state = self._check_facebook(state)
            items.extend(fb_items)
        else:
            self.logger.info("Facebook not configured -- skipping (set FACEBOOK_ACCESS_TOKEN + FACEBOOK_PAGE_ID)")

        if self.tw_bearer and self.tw_access:
            tw_items, state = self._check_twitter(state)
            items.extend(tw_items)
        else:
            self.logger.info("Twitter not configured -- skipping (set TWITTER_BEARER_TOKEN + TWITTER_ACCESS_TOKEN)")

        _save_state(state)
        return items

    def create_action_file(self, item: dict) -> "Path | None":
        """Route to the correct task file based on item['platform']."""
        platform = item.get("platform")
        if platform == "facebook":
            return self._write_fb_task(item)
        elif platform == "twitter":
            return self._write_twitter_task(item)
        return None

    # ── Private: data fetching ────────────────────────────────────────────────

    def _check_facebook(self, state: dict) -> "tuple[list, dict]":
        try:
            resp = requests.get(
                f"{GRAPH_API}/{self.fb_page_id}/posts",
                params={
                    "access_token": self.fb_token,
                    "fields": "id,message,created_time",
                    "limit": 5,
                },
                timeout=20,
            )
            resp.raise_for_status()
            posts = resp.json().get("data", [])

            new_comments = []
            for post in posts:
                cresp = requests.get(
                    f"{GRAPH_API}/{post['id']}/comments",
                    params={
                        "access_token": self.fb_token,
                        "fields": "id,message,from,created_time",
                        "filter": "stream",
                    },
                    timeout=20,
                )
                cresp.raise_for_status()
                comments = cresp.json().get("data", [])

                for c in comments:
                    created = c.get("created_time", "")
                    if (
                        state.get("last_fb_comment_time")
                        and created <= state["last_fb_comment_time"]
                    ):
                        continue
                    new_comments.append({
                        "post_preview": post.get("message", "")[:60],
                        "comment": c.get("message", ""),
                        "from": c.get("from", {}).get("name", "Unknown"),
                        "comment_id": c.get("id", ""),
                        "created": created,
                    })

            if new_comments:
                state["last_fb_comment_time"] = max(c["created"] for c in new_comments)
                return [{"platform": "facebook", "comments": new_comments}], state

        except Exception as exc:
            self.logger.error(f"Facebook watcher error (graceful degradation): {exc}")

        return [], state

    def _check_twitter(self, state: dict) -> "tuple[list, dict]":
        try:
            import tweepy
            client = tweepy.Client(
                bearer_token=self.tw_bearer,
                consumer_key=os.getenv("TWITTER_API_KEY"),
                consumer_secret=os.getenv("TWITTER_API_SECRET"),
                access_token=self.tw_access,
                access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
            )
            me = client.get_me()
            user_id = me.data.id

            kwargs = {
                "max_results": 10,
                "tweet_fields": ["created_at", "text", "author_id"],
            }
            if state.get("last_twitter_mention_id"):
                kwargs["since_id"] = state["last_twitter_mention_id"]

            mentions = client.get_users_mentions(user_id, **kwargs)

            if mentions.data:
                state["last_twitter_mention_id"] = str(mentions.data[0].id)
                return [{"platform": "twitter", "mentions": mentions.data}], state

        except ImportError:
            self.logger.info("tweepy not installed -- skipping Twitter check")
        except Exception as exc:
            self.logger.error(f"Twitter watcher error (graceful degradation): {exc}")

        return [], state

    # ── Private: file writing ─────────────────────────────────────────────────

    def _write_fb_task(self, item: dict) -> Path:
        comments = item["comments"]
        filename = f"{self.datestamp()}_fb-comments-to-reply.md"
        lines = "\n".join(
            f"| {c['from']} | {c['comment'][:80]} | {c['created'][:10]} |"
            for c in comments[:10]
        )
        content = (
            f"# Task: Reply to Facebook Comments\n\n"
            f"> Status: **New**\n> Created: {self.datestamp()}\n"
            f"> Priority: Medium\n> Owner: --\n"
            f"> Type: social_reply\n> Source: social_media_watcher\n> Platform: Facebook\n\n---\n\n"
            f"## Description\n\n{len(comments)} new comment(s) on your Facebook posts need replies.\n"
            f"Draft friendly, on-brand responses using `Company_Handbook.md` tone guidelines.\n\n"
            f"## Comments to Reply\n\n"
            f"| From | Comment | Date |\n|------|---------|------|\n{lines}\n\n"
            f"## Acceptance Criteria\n\n"
            f"- [ ] Replies drafted for all comments\n"
            f"- [ ] Drafts routed to /Pending_Approval/ for human review\n"
        )
        path = self.write_task(self.inbox, filename, content)
        self.logger.info(f"FB COMMENTS: {len(comments)} new >> {filename}")
        self.log_event("facebook.new_comments", {"count": len(comments)})
        return path

    def _write_twitter_task(self, item: dict) -> Path:
        mentions = item["mentions"]
        filename = f"{self.datestamp()}_twitter-mentions.md"
        lines = "\n".join(
            f"| {t.id} | {t.text[:80]} | "
            f"{str(t.created_at)[:10] if t.created_at else ''} |"
            for t in mentions[:10]
        )
        content = (
            f"# Task: Respond to Twitter/X Mentions\n\n"
            f"> Status: **New**\n> Created: {self.datestamp()}\n"
            f"> Priority: Medium\n> Owner: --\n"
            f"> Type: social_reply\n> Source: social_media_watcher\n> Platform: Twitter\n\n---\n\n"
            f"## Description\n\n{len(mentions)} new @mention(s) on Twitter/X.\n"
            f"Draft replies using `Company_Handbook.md` tone guidelines.\n\n"
            f"## Mentions\n\n"
            f"| Tweet ID | Text | Date |\n|----------|------|------|\n{lines}\n\n"
            f"## Acceptance Criteria\n\n"
            f"- [ ] Replies drafted for relevant mentions\n"
            f"- [ ] Drafts routed to /Pending_Approval/ for review\n"
        )
        path = self.write_task(self.inbox, filename, content)
        self.logger.info(f"TWITTER MENTIONS: {len(mentions)} new >> {filename}")
        self.log_event("twitter.new_mentions", {"count": len(mentions)})
        return path


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--loop", action="store_true")
    args = parser.parse_args()

    watcher = SocialMediaWatcher()

    if args.loop:
        print(f"[Social Media Sentinel] Polling every {POLL_INTERVAL // 60} minutes.\n")
        watcher.run()
    else:
        watcher.run_once()


if __name__ == "__main__":
    main()
