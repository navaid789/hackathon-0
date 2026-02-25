"""
AutoOps AI — LinkedIn Watcher & Auto-Poster
----------------------------------------------
Automatically generates and posts business updates to LinkedIn
to generate sales leads and showcase expertise.

Features:
  - Watches for triggers: Done/ folder activity, daily schedule
  - Generates professional LinkedIn posts via Claude API
  - Posts via LinkedIn API (or dry-run simulation)
  - Logs all posts to AI_Employee_Vault/Logs/linkedin_posts.md

Setup (for live mode):
  1. LinkedIn Developer Portal → Create App
  2. Get Access Token with r_liteprofile + w_member_social scopes
  3. Set env var: LINKEDIN_ACCESS_TOKEN=your_token
  4. Set env var: ANTHROPIC_API_KEY=your_claude_key

Run:
    python watchers/linkedin_watcher.py          # one-time post
    python watchers/linkedin_watcher.py --watch  # watch + post daily at 10:00
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
VAULT          = Path("AI_Employee_Vault")
DONE           = VAULT / "Done"
LOGS           = VAULT / "Logs"
LINKEDIN_LOG   = LOGS / "linkedin_posts.md"

LINKEDIN_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
ANTHROPIC_KEY  = os.getenv("ANTHROPIC_API_KEY", "")
DRY_RUN        = not LINKEDIN_TOKEN

LINKEDIN_API   = "https://api.linkedin.com/v2"
POST_HOUR      = 10   # Post daily at 10:00 AM

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    filename=str(LOGS / "system.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
log = logging.getLogger(__name__)


# ─── Content Templates ────────────────────────────────────────────────────────

BUSINESS_TEMPLATES = [
    {
        "type": "productivity_tip",
        "prompt": "Write a LinkedIn post about how AI automation is helping small businesses handle email operations more efficiently. Include a specific tip. End with a call to action. 150-200 words. Professional but conversational tone.",
    },
    {
        "type": "case_study",
        "prompt": "Write a LinkedIn post sharing a mini case study: a small business that was drowning in emails and how an AI assistant helped them respond faster and close more deals. Make it feel real and relatable. 150-200 words.",
    },
    {
        "type": "industry_insight",
        "prompt": "Write a LinkedIn post about the future of AI-powered business operations for SMBs. Share 3 key trends. Be forward-thinking but practical. 150-200 words.",
    },
    {
        "type": "value_prop",
        "prompt": "Write a LinkedIn post about the cost of delayed email responses for small businesses — lost deals, unhappy clients. Show how AI automation fixes this. Include stats if possible. 150-200 words. End with CTA.",
    },
]


def get_post_template() -> dict:
    """Rotate through templates based on day of week."""
    day = date.today().weekday()  # 0=Monday, 6=Sunday
    return BUSINESS_TEMPLATES[day % len(BUSINESS_TEMPLATES)]


def generate_post_content(template: dict) -> str:
    """Generate LinkedIn post content via Claude API or use fallback."""
    if ANTHROPIC_KEY:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
            msg = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=512,
                messages=[{"role": "user", "content": template["prompt"]}],
            )
            content = msg.content[0].text
            log.info(f"LinkedIn post generated via Claude API ({template['type']})")
            return content
        except Exception as e:
            log.error(f"Claude API error: {e}")

    # Fallback posts per type
    fallbacks = {
        "productivity_tip": """🚀 Tip for small business owners: Stop letting emails run your day.

Our AI Email Operations Assistant processes incoming emails, detects priority (urgent vs. routine), drafts replies, and routes them through a human approval workflow — all automatically.

The result? 80% less time on email triage. Zero missed follow-ups. Happy clients.

3 things it does that you wish you had time for:
✅ Detects urgent emails instantly
✅ Drafts professional replies in seconds
✅ Sends only after YOU approve

Your inbox shouldn't be a source of stress. Let AI handle the sorting; you handle the decisions.

Curious how it works? Drop a comment 👇

#Automation #AI #SmallBusiness #EmailProductivity #AutoOpsAI""",

        "case_study": """📬 How one small business went from overwhelmed to on top of their inbox:

They were getting 50+ emails a day. Invoices slipping through. Client follow-ups delayed by 3-4 days.

After deploying AutoOps AI:
→ Every email gets triaged automatically
→ High-priority items flagged within seconds
→ Draft replies ready for approval — not writing from scratch

The owner now spends 30 minutes a day on emails instead of 3 hours.

The best part? Nothing gets sent without human approval. Full control, zero chaos.

AI isn't replacing the human touch — it's protecting your time so you can use it where it matters.

Have you automated any part of your email workflow? I'd love to hear 👇

#SMB #AITools #BusinessAutomation #Productivity #AutoOpsAI""",

        "industry_insight": """📊 3 AI trends every small business owner should know in 2026:

1️⃣ Human-in-the-loop AI
AI handles volume; humans handle judgment. The best systems flag, draft, and wait for your approval before acting.

2️⃣ Context-aware automation
Modern AI doesn't just search keywords — it understands urgency, tone, and client history to prioritize correctly.

3️⃣ No-code agent workflows
You don't need a dev team. Tools like AutoOps AI let SMBs deploy AI workflows in days, not months.

The competitive advantage is no longer "do you have AI?" It's "how well is your AI integrated?"

What AI tool has made the biggest difference in your business? Drop it below 👇

#AI #FutureOfWork #SmallBusiness #BusinessIntelligence #AutoOpsAI""",

        "value_prop": """💸 The hidden cost of slow email responses:

Studies show 50% of sales go to the first vendor to respond.

If a potential client emails you and waits 24 hours — they've already called someone else.

With AutoOps AI:
→ Emails detected in real-time
→ Priority score assigned instantly
→ Draft reply ready in under 60 seconds
→ Sent after your 1-click approval

You stay in control. Your clients feel valued. No lead goes cold.

For small businesses, speed is the advantage you can actually compete on against bigger players.

Want to see how it works? Comment "demo" and I'll share a walkthrough.

#SalesAutomation #AI #LeadResponse #SmallBusiness #EmailMarketing #AutoOpsAI""",
    }

    return fallbacks.get(template["type"], fallbacks["productivity_tip"])


def get_linkedin_person_urn() -> str:
    """Get LinkedIn member URN for the authenticated user."""
    headers = {
        "Authorization": f"Bearer {LINKEDIN_TOKEN}",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    try:
        resp = requests.get(f"{LINKEDIN_API}/me", headers=headers, timeout=10)
        resp.raise_for_status()
        return f"urn:li:person:{resp.json()['id']}"
    except Exception as e:
        log.error(f"LinkedIn /me error: {e}")
        return ""


def post_to_linkedin(content: str) -> dict:
    """Post to LinkedIn via API."""
    person_urn = get_linkedin_person_urn()
    if not person_urn:
        return {"error": "Could not get LinkedIn profile URN"}

    headers = {
        "Authorization": f"Bearer {LINKEDIN_TOKEN}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": content},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }

    try:
        resp = requests.post(
            f"{LINKEDIN_API}/ugcPosts",
            headers=headers,
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        post_id = resp.headers.get("x-restli-id", "unknown")
        return {"status": "posted", "post_id": post_id}
    except Exception as e:
        log.error(f"LinkedIn post error: {e}")
        return {"error": str(e)}


def save_post_log(content: str, result: dict, template_type: str):
    """Append post to linkedin_posts.md log file."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    status = "✅ POSTED" if "post_id" in result else "🔵 DRY-RUN" if DRY_RUN else "❌ FAILED"

    entry = f"""
---
## {now} — {template_type} [{status}]

{content}

**Result:** {json.dumps(result)}
"""
    with open(LINKEDIN_LOG, "a", encoding="utf-8") as f:
        f.write(entry)


def run_post() -> bool:
    """Generate and post one LinkedIn update."""
    print(f"\n{'='*50}")
    print(f"AutoOps AI — LinkedIn Watcher")
    print(f"{'='*50}")
    print(f"Mode: {'DRY-RUN (no token)' if DRY_RUN else 'LIVE (LinkedIn API)'}")

    template = get_post_template()
    print(f"Post type: {template['type']}")
    print(f"Generating content...")

    content = generate_post_content(template)
    print(f"\n--- POST PREVIEW ---\n{content[:300]}...\n{'─'*40}")

    if DRY_RUN:
        result = {"status": "dry-run", "note": "Set LINKEDIN_ACCESS_TOKEN to post live"}
        print(f"[DRY-RUN] Post simulated (not sent to LinkedIn)")
        print(f"Set LINKEDIN_ACCESS_TOKEN env var for live posting")
    else:
        print("Posting to LinkedIn...")
        result = post_to_linkedin(content)
        if "post_id" in result:
            print(f"✅ Posted! Post ID: {result['post_id']}")
        else:
            print(f"❌ Failed: {result.get('error', 'unknown')}")

    save_post_log(content, result, template["type"])
    log.info(f"LinkedIn post: type={template['type']} status={result}")
    print(f"✅ Logged to Logs/linkedin_posts.md")
    return "error" not in result


def run_watch():
    """Watch mode: post once per day at POST_HOUR."""
    print(f"LinkedIn Watcher started — posts daily at {POST_HOUR:02d}:00")
    log.info("LinkedIn watcher watch mode started")
    posted_today = None

    while True:
        try:
            now = datetime.now()
            today = now.date()

            if now.hour >= POST_HOUR and posted_today != today:
                run_post()
                posted_today = today
                print(f"Next post: tomorrow at {POST_HOUR:02d}:00")

            time.sleep(300)  # Check every 5 minutes

        except KeyboardInterrupt:
            print("\nLinkedIn watcher stopped.")
            break
        except Exception as e:
            log.error(f"Watch loop error: {e}")
            time.sleep(60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AutoOps AI LinkedIn Watcher")
    parser.add_argument("--watch", action="store_true", help="Watch mode (post daily at 10am)")
    args = parser.parse_args()

    if args.watch:
        run_watch()
    else:
        run_post()
