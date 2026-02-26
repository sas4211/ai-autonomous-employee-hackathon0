"""
MCP Server: Social Media
=========================
FastMCP server exposing Facebook, Instagram, and Twitter/X APIs to Claude Code.

Tools:
  post_to_facebook(content)             - Post to Facebook Page
  post_to_instagram(caption, image_url) - Post image to Instagram Business
  post_to_twitter(content)              - Post tweet (Twitter/X API v2)
  get_social_summary(days)              - Cross-platform engagement summary
  get_facebook_insights()               - FB page reach/engagement
  get_twitter_mentions(count)           - Recent @mentions
  get_instagram_insights()              - IG post performance

All post tools require prior human approval in /Approved/.
Read/insights tools are always safe.

Setup:
  Facebook/Instagram:
    1. Create a Meta App: https://developers.facebook.com/
    2. Add Facebook Login + Instagram API scopes
    3. Generate a long-lived Page Access Token
    4. Set FACEBOOK_ACCESS_TOKEN, FACEBOOK_PAGE_ID, INSTAGRAM_ACCOUNT_ID in .env

  Twitter/X:
    1. Create an app: https://developer.twitter.com/
    2. Enable OAuth 2.0 and generate bearer + access tokens
    3. Set TWITTER_* credentials in .env

Usage:
    python mcp_servers/social_media.py           # stdio MCP mode
    python mcp_servers/social_media.py --test    # self-test
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    import requests
    from dotenv import load_dotenv
    from fastmcp import FastMCP
except ImportError:
    print("ERROR: Run: pip install fastmcp requests python-dotenv", file=sys.stderr)
    sys.exit(1)

VAULT_ROOT = Path(__file__).parent.parent
LOGS = VAULT_ROOT / "Logs"
load_dotenv(VAULT_ROOT / ".env")

mcp = FastMCP(
    name="ai-employee-social-media",
    instructions=(
        "Social media server for Facebook, Instagram, and Twitter/X. "
        "Post tools require prior human approval. "
        "Insights/read tools are always safe to call."
    ),
)

GRAPH_API = "https://graph.facebook.com/v19.0"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _datestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _write_log(action: str, payload: dict, result: str):
    LOGS.mkdir(exist_ok=True)
    log_file = LOGS / f"{_datestamp()}_social_media_actions.md"
    mode = "a" if log_file.exists() else "w"
    with log_file.open(mode, encoding="utf-8") as f:
        f.write(
            f"\n## {action} — {_now()}\n\n"
            f"```json\n{json.dumps(payload, indent=2)}\n```\n\n"
            f"**Result:** {result}\n"
        )


def _graph_get(path: str, params: dict) -> dict:
    params.setdefault("access_token", os.getenv("FACEBOOK_ACCESS_TOKEN", ""))
    resp = requests.get(f"{GRAPH_API}/{path}", params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _graph_post(path: str, data: dict) -> dict:
    data.setdefault("access_token", os.getenv("FACEBOOK_ACCESS_TOKEN", ""))
    resp = requests.post(f"{GRAPH_API}/{path}", data=data, timeout=30)
    resp.raise_for_status()
    return resp.json()


# ── Facebook Tools ────────────────────────────────────────────────────────────

@mcp.tool()
def post_to_facebook(content: str, link: str = "") -> str:
    """
    Publish a text post to the Facebook Page.
    REQUIRES prior human approval — only call after task is in /Approved/.

    Args:
        content: The post text (up to 63,206 characters)
        link:    Optional URL to attach to the post

    Returns:
        Post ID on success, or error description.
    """
    page_id = os.getenv("FACEBOOK_PAGE_ID")
    if not page_id or not os.getenv("FACEBOOK_ACCESS_TOKEN"):
        return "ERROR: FACEBOOK_PAGE_ID and FACEBOOK_ACCESS_TOKEN not set in .env"

    try:
        data = {"message": content}
        if link:
            data["link"] = link
        result = _graph_post(f"{page_id}/feed", data)
        post_id = result.get("id", "unknown")
        _write_log("facebook_post", {"content_preview": content[:100]}, f"Success — ID: {post_id}")
        return f"Facebook post published. Post ID: {post_id}"
    except requests.HTTPError as exc:
        _write_log("facebook_post", {"content_preview": content[:100]}, f"FAILED: {exc}")
        return f"ERROR posting to Facebook: {exc}"


@mcp.tool()
def post_to_instagram(caption: str, image_url: str) -> str:
    """
    Publish an image post to Instagram Business account.
    REQUIRES prior human approval — only call after task is in /Approved/.

    Args:
        caption:   Post caption text (include hashtags here)
        image_url: Public URL of the image to post (JPEG/PNG, min 320px)

    Returns:
        Media ID on success, or error description.
    """
    ig_account_id = os.getenv("INSTAGRAM_ACCOUNT_ID")
    if not ig_account_id or not os.getenv("FACEBOOK_ACCESS_TOKEN"):
        return "ERROR: INSTAGRAM_ACCOUNT_ID and FACEBOOK_ACCESS_TOKEN not set in .env"

    try:
        # Step 1: Create media container
        container = _graph_post(f"{ig_account_id}/media", {
            "caption": caption,
            "image_url": image_url,
            "media_type": "IMAGE",
        })
        creation_id = container.get("id")
        if not creation_id:
            return f"ERROR: Failed to create media container. Response: {container}"

        # Step 2: Publish the container
        result = _graph_post(f"{ig_account_id}/media_publish", {
            "creation_id": creation_id
        })
        media_id = result.get("id", "unknown")
        _write_log("instagram_post", {"caption_preview": caption[:80]}, f"Success — ID: {media_id}")
        return f"Instagram post published. Media ID: {media_id}"

    except requests.HTTPError as exc:
        _write_log("instagram_post", {"caption_preview": caption[:80]}, f"FAILED: {exc}")
        return f"ERROR posting to Instagram: {exc}"


@mcp.tool()
def get_facebook_insights(days: int = 7) -> str:
    """
    Get Facebook Page engagement metrics for the last N days.

    Args:
        days: Number of days to look back (default 7, max 90)

    Returns:
        JSON with reach, impressions, engagement, page likes.
    """
    page_id = os.getenv("FACEBOOK_PAGE_ID")
    if not page_id or not os.getenv("FACEBOOK_ACCESS_TOKEN"):
        return json.dumps({"error": "FACEBOOK_PAGE_ID and FACEBOOK_ACCESS_TOKEN not set in .env"})

    try:
        metrics = "page_impressions,page_reach,page_engaged_users,page_fans"
        since = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp())
        data = _graph_get(f"{page_id}/insights", {
            "metric": metrics,
            "period": "day",
            "since": since,
        })
        summary = {}
        for metric in data.get("data", []):
            name = metric["name"]
            values = metric.get("values", [])
            total = sum(v.get("value", 0) for v in values if isinstance(v.get("value"), (int, float)))
            summary[name] = total

        # Recent posts
        posts = _graph_get(f"{page_id}/posts", {
            "fields": "message,created_time,likes.summary(true),comments.summary(true)",
            "limit": 5,
        })

        return json.dumps({
            "period_days": days,
            "metrics": summary,
            "recent_posts": [{
                "message_preview": p.get("message", "")[:80],
                "created": p.get("created_time", ""),
                "likes": p.get("likes", {}).get("summary", {}).get("total_count", 0),
                "comments": p.get("comments", {}).get("summary", {}).get("total_count", 0),
            } for p in posts.get("data", [])],
        }, indent=2)

    except Exception as exc:
        return json.dumps({"error": str(exc)})


@mcp.tool()
def get_instagram_insights(days: int = 7) -> str:
    """
    Get Instagram Business account engagement metrics.

    Args:
        days: Number of days to look back (default 7)

    Returns:
        JSON with follower count, impressions, reach, recent post performance.
    """
    ig_account_id = os.getenv("INSTAGRAM_ACCOUNT_ID")
    if not ig_account_id or not os.getenv("FACEBOOK_ACCESS_TOKEN"):
        return json.dumps({"error": "INSTAGRAM_ACCOUNT_ID and FACEBOOK_ACCESS_TOKEN not set in .env"})

    try:
        # Account info
        account = _graph_get(ig_account_id, {
            "fields": "followers_count,media_count,name,username"
        })

        # Recent media
        media = _graph_get(f"{ig_account_id}/media", {
            "fields": "caption,timestamp,like_count,comments_count,media_type",
            "limit": 5,
        })

        since = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp())
        insights = _graph_get(f"{ig_account_id}/insights", {
            "metric": "impressions,reach,profile_views",
            "period": "day",
            "since": since,
        })

        metric_totals = {}
        for m in insights.get("data", []):
            metric_totals[m["name"]] = sum(
                v.get("value", 0) for v in m.get("values", [])
                if isinstance(v.get("value"), (int, float))
            )

        return json.dumps({
            "account": account.get("username", ""),
            "followers": account.get("followers_count", 0),
            "total_posts": account.get("media_count", 0),
            "period_days": days,
            "metrics": metric_totals,
            "recent_posts": [{
                "caption_preview": p.get("caption", "")[:80],
                "type": p.get("media_type", ""),
                "timestamp": p.get("timestamp", ""),
                "likes": p.get("like_count", 0),
                "comments": p.get("comments_count", 0),
            } for p in media.get("data", [])],
        }, indent=2)

    except Exception as exc:
        return json.dumps({"error": str(exc)})


# ── Twitter/X Tools ───────────────────────────────────────────────────────────

def _twitter_client():
    try:
        import tweepy
    except ImportError:
        raise RuntimeError("tweepy not installed. Run: pip install tweepy")

    return tweepy.Client(
        bearer_token=os.getenv("TWITTER_BEARER_TOKEN"),
        consumer_key=os.getenv("TWITTER_API_KEY"),
        consumer_secret=os.getenv("TWITTER_API_SECRET"),
        access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
        access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
        wait_on_rate_limit=True,
    )


@mcp.tool()
def post_to_twitter(content: str) -> str:
    """
    Post a tweet via Twitter/X API v2.
    REQUIRES prior human approval — only call after task is in /Approved/.

    Args:
        content: Tweet text (max 280 characters)

    Returns:
        Tweet ID on success, or error description.
    """
    if len(content) > 280:
        return f"ERROR: Tweet too long ({len(content)} chars). Max 280."

    if not os.getenv("TWITTER_ACCESS_TOKEN"):
        return "ERROR: TWITTER_ACCESS_TOKEN not set in .env"

    try:
        client = _twitter_client()
        response = client.create_tweet(text=content)
        tweet_id = response.data["id"]
        _write_log("twitter_post", {"content_preview": content[:100]}, f"Success — ID: {tweet_id}")
        return f"Tweet posted. Tweet ID: {tweet_id}. URL: https://twitter.com/i/web/status/{tweet_id}"
    except Exception as exc:
        _write_log("twitter_post", {"content_preview": content[:100]}, f"FAILED: {exc}")
        return f"ERROR posting to Twitter: {exc}"


@mcp.tool()
def get_twitter_mentions(count: int = 10) -> str:
    """
    Get recent @mentions of your Twitter/X account.

    Args:
        count: Number of recent mentions to retrieve (default 10, max 100)

    Returns:
        JSON list of recent mentions with author, text, timestamp.
    """
    if not os.getenv("TWITTER_BEARER_TOKEN"):
        return json.dumps({"error": "TWITTER_BEARER_TOKEN not set in .env"})

    try:
        client = _twitter_client()
        # Get authenticated user ID first
        me = client.get_me()
        user_id = me.data.id

        mentions = client.get_users_mentions(
            user_id, max_results=min(count, 100),
            tweet_fields=["created_at", "author_id", "text"]
        )
        results = []
        if mentions.data:
            for tweet in mentions.data:
                results.append({
                    "id": str(tweet.id),
                    "text": tweet.text,
                    "created_at": str(tweet.created_at) if tweet.created_at else "",
                })
        return json.dumps({"mentions": results, "count": len(results)}, indent=2)

    except Exception as exc:
        return json.dumps({"error": str(exc)})


@mcp.tool()
def get_social_summary(days: int = 7) -> str:
    """
    Generate a cross-platform social media summary for the last N days.
    Aggregates Facebook, Instagram, and Twitter metrics in one report.

    Args:
        days: Number of days to look back (default 7)

    Returns:
        JSON summary across all three platforms.
    """
    summary = {"period_days": days, "generated_at": _now(), "platforms": {}}

    # Facebook
    try:
        fb_data = json.loads(get_facebook_insights(days))
        if "error" not in fb_data:
            summary["platforms"]["facebook"] = {
                "reach": fb_data.get("metrics", {}).get("page_reach", 0),
                "impressions": fb_data.get("metrics", {}).get("page_impressions", 0),
                "engaged_users": fb_data.get("metrics", {}).get("page_engaged_users", 0),
                "recent_posts": len(fb_data.get("recent_posts", [])),
            }
        else:
            summary["platforms"]["facebook"] = {"status": "unavailable", "reason": fb_data["error"]}
    except Exception as exc:
        summary["platforms"]["facebook"] = {"status": "error", "reason": str(exc)}

    # Instagram
    try:
        ig_data = json.loads(get_instagram_insights(days))
        if "error" not in ig_data:
            summary["platforms"]["instagram"] = {
                "followers": ig_data.get("followers", 0),
                "reach": ig_data.get("metrics", {}).get("reach", 0),
                "impressions": ig_data.get("metrics", {}).get("impressions", 0),
                "recent_posts": len(ig_data.get("recent_posts", [])),
            }
        else:
            summary["platforms"]["instagram"] = {"status": "unavailable", "reason": ig_data["error"]}
    except Exception as exc:
        summary["platforms"]["instagram"] = {"status": "error", "reason": str(exc)}

    # Twitter
    try:
        tw_data = json.loads(get_twitter_mentions(5))
        if "error" not in tw_data:
            summary["platforms"]["twitter"] = {
                "recent_mentions": tw_data.get("count", 0),
            }
        else:
            summary["platforms"]["twitter"] = {"status": "unavailable", "reason": tw_data["error"]}
    except Exception as exc:
        summary["platforms"]["twitter"] = {"status": "error", "reason": str(exc)}

    return json.dumps(summary, indent=2)


# ── Entry point ───────────────────────────────────────────────────────────────

def _self_test():
    print("=== Social Media MCP Server - Self Test ===\n")
    tools = [post_to_facebook, post_to_instagram, post_to_twitter,
             get_facebook_insights, get_instagram_insights,
             get_twitter_mentions, get_social_summary]
    for t in tools:
        print(f"  [OK] {t.__name__}")

    creds = {
        "FACEBOOK_ACCESS_TOKEN": bool(os.getenv("FACEBOOK_ACCESS_TOKEN")),
        "FACEBOOK_PAGE_ID": bool(os.getenv("FACEBOOK_PAGE_ID")),
        "INSTAGRAM_ACCOUNT_ID": bool(os.getenv("INSTAGRAM_ACCOUNT_ID")),
        "TWITTER_BEARER_TOKEN": bool(os.getenv("TWITTER_BEARER_TOKEN")),
        "TWITTER_ACCESS_TOKEN": bool(os.getenv("TWITTER_ACCESS_TOKEN")),
    }
    print("\nCredentials in .env:")
    for k, v in creds.items():
        print(f"  {k}: {'[SET]' if v else '[NOT SET]'}")

    print("\n[OK] Server ready.")


def main():
    if "--test" in sys.argv:
        _self_test()
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
