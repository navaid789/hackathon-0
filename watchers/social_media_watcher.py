"""
AutoOps AI — Social Media Watcher
------------------------------------
Auto-posts business updates to Facebook, Instagram, and Twitter (X)
and generates engagement summaries.

Platforms:
  - Facebook Pages (via Graph API)
  - Instagram Business (via Graph API)
  - Twitter/X (via Twitter API v2)

Setup:
  Facebook/Instagram:
    FB_PAGE_ACCESS_TOKEN=your_token
    FB_PAGE_ID=your_page_id
    IG_USER_ID=your_instagram_business_id

  Twitter/X:
    TWITTER_BEARER_TOKEN=your_bearer_token
    TWITTER_API_KEY=your_api_key
    TWITTER_API_SECRET=your_api_secret
    TWITTER_ACCESS_TOKEN=your_access_token
    TWITTER_ACCESS_SECRET=your_access_secret

Run:
    python watchers/social_media_watcher.py              # one-time post to all
    python watchers/social_media_watcher.py --platform facebook
    python watchers/social_media_watcher.py --platform twitter
    python watchers/social_media_watcher.py --watch      # daily at 11:00 AM
    python watchers/social_media_watcher.py --summary    # fetch engagement summary
"""

import os
import time
import json
import logging
import argparse
import requests
from pathlib import Path
from datetime import datetime, date

# ─── Config ───────────────────────────────────────────────────────────────────
VAULT    = Path("AI_Employee_Vault")
LOGS     = VAULT / "Logs"
SOCIAL_LOG = LOGS / "social_media_posts.md"

# Facebook / Instagram
FB_TOKEN   = os.getenv("FB_PAGE_ACCESS_TOKEN", "")
FB_PAGE_ID = os.getenv("FB_PAGE_ID", "")
IG_USER_ID = os.getenv("IG_USER_ID", "")

# Twitter / X
TW_BEARER       = os.getenv("TWITTER_BEARER_TOKEN", "")
TW_API_KEY      = os.getenv("TWITTER_API_KEY", "")
TW_API_SECRET   = os.getenv("TWITTER_API_SECRET", "")
TW_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "")
TW_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET", "")

ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
POST_HOUR     = 11

FB_LIVE = bool(FB_TOKEN and FB_PAGE_ID)
IG_LIVE = bool(FB_TOKEN and IG_USER_ID)
TW_LIVE = bool(TW_API_KEY and TW_ACCESS_TOKEN)

logging.basicConfig(
    filename=str(LOGS / "system.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
log = logging.getLogger(__name__)

# ─── Content Generation ───────────────────────────────────────────────────────

POST_TEMPLATES = {
    "facebook": [
        "Write a Facebook business post (200-250 words) about how AI automation helps small businesses save time on email operations. Include a story element. End with a question to encourage comments. Include relevant emojis.",
        "Write a Facebook post sharing 5 quick tips for small business owners to improve their email response time using AI tools. Make it engaging and practical. Include emojis.",
    ],
    "instagram": [
        "Write an Instagram caption (150 words max) about AI-powered business automation. Make it visually descriptive, aspirational, include 10-15 relevant hashtags at the end.",
        "Write an Instagram caption for a 'day in the life of an AI assistant' theme. Keep it relatable and engaging. Include hashtags. Max 150 words.",
    ],
    "twitter": [
        "Write a Twitter/X thread (3 tweets) about AI email automation for small businesses. Tweet 1: hook. Tweet 2: key benefit. Tweet 3: CTA. Each tweet max 280 chars. Format as: [1/3] ... [2/3] ... [3/3]",
        "Write a single compelling tweet (max 280 chars) about the cost of slow email responses for businesses. Include relevant hashtags. Sharp and punchy.",
    ],
}

FALLBACK_POSTS = {
    "facebook": """🚀 Is your email inbox running your business instead of YOU running your business?

We built AutoOps AI — an autonomous email assistant that reads, prioritizes, and drafts responses to every email that comes in.

Here's how it works:
📥 Email arrives → instantly detected
🔴 Priority flagged (urgent, invoice, meeting)
✍️ Draft reply prepared in seconds
✅ YOU approve with one click
📤 Email sent — client happy

The result? Our users spend 80% less time on email triage and ZERO time worrying about missed follow-ups.

The best part? Nothing gets sent without your approval. Full control, zero chaos.

Question for you: What's the #1 thing eating your time as a business owner? Drop it below 👇

#SmallBusiness #AITools #Automation #Productivity #EmailMarketing #BusinessGrowth""",

    "instagram": """Your inbox shouldn't run your business. You should. 📱✨

AutoOps AI reads every email, flags what's urgent, drafts the reply — and waits for YOU to say go.

80% less email time. 100% human control. 🎯

Drop a 🙋 if your inbox is out of control!

#AutoOpsAI #SmallBusiness #AIAssistant #EmailAutomation #BusinessOwner #Entrepreneur #ProductivityHacks #WorkSmart #AITools #BusinessGrowth #Automation #TimeManagement #SmallBiz #Startup #TechForBusiness""",

    "twitter": """[1/3] 50% of sales go to whoever responds first.

If a lead emails you and waits 24hrs — they've already moved on. 🧵

[2/3] AutoOps AI detects emails instantly, detects priority, and has a draft reply ready in seconds.

You approve → it sends. Nothing goes out without you.

[3/3] Speed is the advantage small businesses can actually compete on.

Don't let your inbox cost you deals.

What's your current email response time? 👇

#AI #SalesAutomation #SmallBusiness #EmailMarketing""",
}


def generate_content(platform: str) -> str:
    """Generate post content via Claude API or fallback."""
    if ANTHROPIC_KEY:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
            templates = POST_TEMPLATES.get(platform, POST_TEMPLATES["facebook"])
            day_idx = date.today().weekday() % len(templates)
            msg = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=512,
                messages=[{"role": "user", "content": templates[day_idx]}],
            )
            return msg.content[0].text
        except Exception as e:
            log.error(f"Claude API error for {platform}: {e}")

    return FALLBACK_POSTS.get(platform, FALLBACK_POSTS["facebook"])


# ─── Facebook ────────────────────────────────────────────────────────────────

def post_facebook(content: str) -> dict:
    if not FB_LIVE:
        return {"dry_run": True, "platform": "facebook", "preview": content[:100]}
    try:
        resp = requests.post(
            f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed",
            params={"access_token": FB_TOKEN},
            json={"message": content},
            timeout=15,
        )
        resp.raise_for_status()
        return {"platform": "facebook", "post_id": resp.json().get("id"), "status": "posted"}
    except Exception as e:
        log.error(f"Facebook post error: {e}")
        return {"platform": "facebook", "error": str(e)}


def get_facebook_summary() -> str:
    if not FB_LIVE:
        return "[DRY-RUN] Facebook summary — set FB_PAGE_ACCESS_TOKEN + FB_PAGE_ID"
    try:
        resp = requests.get(
            f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/posts",
            params={
                "access_token": FB_TOKEN,
                "fields": "message,created_time,likes.summary(true),comments.summary(true)",
                "limit": 5,
            },
            timeout=10,
        )
        posts = resp.json().get("data", [])
        lines = [f"Facebook Page Summary (last {len(posts)} posts):"]
        for p in posts:
            likes = p.get("likes", {}).get("summary", {}).get("total_count", 0)
            comments = p.get("comments", {}).get("summary", {}).get("total_count", 0)
            preview = (p.get("message", "")[:60] + "...") if p.get("message") else "(no text)"
            lines.append(f"  • {preview} | 👍 {likes} | 💬 {comments}")
        return "\n".join(lines)
    except Exception as e:
        return f"Facebook summary error: {e}"


# ─── Instagram ───────────────────────────────────────────────────────────────

def post_instagram(content: str) -> dict:
    if not IG_LIVE:
        return {"dry_run": True, "platform": "instagram", "preview": content[:100]}
    try:
        # Step 1: Create media container
        media_resp = requests.post(
            f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media",
            params={"access_token": FB_TOKEN},
            json={"caption": content, "media_type": "REELS"},
            timeout=15,
        )
        media_id = media_resp.json().get("id")
        if not media_id:
            return {"platform": "instagram", "error": "Media container creation failed"}

        # Step 2: Publish
        pub_resp = requests.post(
            f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media_publish",
            params={"access_token": FB_TOKEN},
            json={"creation_id": media_id},
            timeout=15,
        )
        pub_resp.raise_for_status()
        return {"platform": "instagram", "post_id": pub_resp.json().get("id"), "status": "posted"}
    except Exception as e:
        log.error(f"Instagram post error: {e}")
        return {"platform": "instagram", "error": str(e)}


def get_instagram_summary() -> str:
    if not IG_LIVE:
        return "[DRY-RUN] Instagram summary — set FB_PAGE_ACCESS_TOKEN + IG_USER_ID"
    try:
        resp = requests.get(
            f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media",
            params={
                "access_token": FB_TOKEN,
                "fields": "caption,like_count,comments_count,timestamp",
                "limit": 5,
            },
            timeout=10,
        )
        posts = resp.json().get("data", [])
        lines = [f"Instagram Summary (last {len(posts)} posts):"]
        for p in posts:
            caption = (p.get("caption", "")[:60] + "...") if p.get("caption") else "(no caption)"
            lines.append(f"  • {caption} | ❤️ {p.get('like_count',0)} | 💬 {p.get('comments_count',0)}")
        return "\n".join(lines)
    except Exception as e:
        return f"Instagram summary error: {e}"


# ─── Twitter / X ─────────────────────────────────────────────────────────────

def post_twitter(content: str) -> dict:
    if not TW_LIVE:
        return {"dry_run": True, "platform": "twitter", "preview": content[:100]}
    try:
        from requests_oauthlib import OAuth1
        auth = OAuth1(TW_API_KEY, TW_API_SECRET, TW_ACCESS_TOKEN, TW_ACCESS_SECRET)

        # Post as thread if [1/3] format detected
        tweets = [t.strip() for t in content.split("\n\n") if t.strip()]
        if not any("[1/" in t for t in tweets):
            tweets = [content[:280]]

        tweet_ids = []
        reply_to = None
        for tweet_text in tweets:
            payload = {"text": tweet_text[:280]}
            if reply_to:
                payload["reply"] = {"in_reply_to_tweet_id": reply_to}

            resp = requests.post(
                "https://api.twitter.com/2/tweets",
                auth=auth,
                json=payload,
                timeout=15,
            )
            resp.raise_for_status()
            tweet_id = resp.json()["data"]["id"]
            tweet_ids.append(tweet_id)
            reply_to = tweet_id

        return {"platform": "twitter", "tweet_ids": tweet_ids, "status": "posted", "count": len(tweet_ids)}
    except Exception as e:
        log.error(f"Twitter post error: {e}")
        return {"platform": "twitter", "error": str(e)}


def get_twitter_summary() -> str:
    if not TW_LIVE:
        return "[DRY-RUN] Twitter summary — set TWITTER_API_KEY + TWITTER_ACCESS_TOKEN"
    try:
        headers = {"Authorization": f"Bearer {TW_BEARER}"}
        # Get own user id first
        me = requests.get("https://api.twitter.com/2/users/me", headers=headers, timeout=10)
        user_id = me.json()["data"]["id"]

        resp = requests.get(
            f"https://api.twitter.com/2/users/{user_id}/tweets",
            headers=headers,
            params={
                "max_results": 5,
                "tweet.fields": "public_metrics,created_at",
            },
            timeout=10,
        )
        tweets = resp.json().get("data", [])
        lines = [f"Twitter/X Summary (last {len(tweets)} tweets):"]
        for t in tweets:
            m = t.get("public_metrics", {})
            preview = t["text"][:60] + "..."
            lines.append(f"  • {preview} | ❤️ {m.get('like_count',0)} | 🔁 {m.get('retweet_count',0)} | 💬 {m.get('reply_count',0)}")
        return "\n".join(lines)
    except Exception as e:
        return f"Twitter summary error: {e}"


# ─── Save Log ─────────────────────────────────────────────────────────────────

def save_log(platform: str, content: str, result: dict):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    dry = result.get("dry_run", False)
    status = "🔵 DRY-RUN" if dry else ("✅ POSTED" if "error" not in result else "❌ FAILED")
    entry = f"\n---\n## {now} — {platform.upper()} [{status}]\n\n{content}\n\n**Result:** {json.dumps(result)}\n"
    with open(SOCIAL_LOG, "a", encoding="utf-8") as f:
        f.write(entry)


# ─── Main ─────────────────────────────────────────────────────────────────────

def run_post(platforms=None):
    if platforms is None:
        platforms = ["facebook", "instagram", "twitter"]

    print(f"\n{'='*55}")
    print(f"AutoOps AI — Social Media Watcher")
    print(f"{'='*55}")
    print(f"Facebook : {'LIVE' if FB_LIVE else 'DRY-RUN'}")
    print(f"Instagram: {'LIVE' if IG_LIVE else 'DRY-RUN'}")
    print(f"Twitter  : {'LIVE' if TW_LIVE else 'DRY-RUN'}")
    print(f"{'='*55}\n")

    for platform in platforms:
        print(f"[{platform.upper()}] Generating content...")
        content = generate_content(platform)
        print(f"  Preview: {content[:80]}...")

        if platform == "facebook":
            result = post_facebook(content)
        elif platform == "instagram":
            result = post_instagram(content)
        elif platform == "twitter":
            result = post_twitter(content)
        else:
            continue

        save_log(platform, content, result)
        status = "DRY-RUN" if result.get("dry_run") else ("✅ POSTED" if "error" not in result else f"❌ {result.get('error')}")
        print(f"  {platform}: {status}")
        log.info(f"Social post {platform}: {result}")


def run_summary():
    print("\n=== SOCIAL MEDIA ENGAGEMENT SUMMARY ===\n")
    print(get_facebook_summary())
    print()
    print(get_instagram_summary())
    print()
    print(get_twitter_summary())


def run_watch():
    print(f"Social Media Watcher — posts daily at {POST_HOUR:02d}:00")
    posted_today = None
    while True:
        try:
            now = datetime.now()
            if now.hour >= POST_HOUR and posted_today != now.date():
                run_post()
                posted_today = now.date()
            time.sleep(300)
        except KeyboardInterrupt:
            print("\nSocial media watcher stopped.")
            break
        except Exception as e:
            log.error(f"Social watcher error: {e}")
            time.sleep(60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AutoOps AI Social Media Watcher")
    parser.add_argument("--watch",    action="store_true", help="Watch mode — post daily at 11am")
    parser.add_argument("--summary",  action="store_true", help="Fetch engagement summary")
    parser.add_argument("--platform", choices=["facebook", "instagram", "twitter"], help="Post to one platform only")
    args = parser.parse_args()

    if args.summary:
        run_summary()
    elif args.watch:
        run_watch()
    else:
        platforms = [args.platform] if args.platform else None
        run_post(platforms)
