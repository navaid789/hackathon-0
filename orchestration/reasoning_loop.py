"""
AutoOps AI — Claude Reasoning Loop
------------------------------------
Automatically reads emails from Needs_Action/,
uses Claude AI to analyze and create Plan.md files in Plans/,
then moves tasks to Pending_Approval/ for human review.

Run:
    python orchestration/reasoning_loop.py              # one-time run
    python orchestration/reasoning_loop.py --watch      # continuous loop (every 60s)
"""

import os
import time
import shutil
import logging
import argparse
from pathlib import Path
from datetime import datetime

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    filename="AI_Employee_Vault/Logs/reasoning_loop.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
log = logging.getLogger(__name__)

# ─── Paths ────────────────────────────────────────────────────────────────────
VAULT          = Path("AI_Employee_Vault")
NEEDS_ACTION   = VAULT / "Needs_Action"
PLANS          = VAULT / "Plans"
PENDING        = VAULT / "Pending_Approval"
DONE           = VAULT / "Done"
PROCESSED_FILE = VAULT / "Logs" / "reasoning_processed.txt"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
DRY_RUN = not ANTHROPIC_API_KEY


def get_processed() -> set:
    """Track already-processed files to avoid duplicates."""
    if not PROCESSED_FILE.exists():
        return set()
    return set(PROCESSED_FILE.read_text().splitlines())


def mark_processed(filename: str):
    with open(PROCESSED_FILE, "a") as f:
        f.write(filename + "\n")


def detect_priority(content: str) -> str:
    text = content.lower()
    if any(w in text for w in ["urgent", "asap", "immediately", "critical", "overdue", "invoice", "payment"]):
        return "HIGH"
    if any(w in text for w in ["meeting", "schedule", "follow-up", "proposal", "contract", "review"]):
        return "MEDIUM"
    return "LOW"


def extract_client(content: str) -> str:
    for line in content.splitlines():
        if line.lower().startswith("**from:**"):
            return line.split("**From:**")[-1].strip()
    return "Unknown Client"


def extract_subject(content: str) -> str:
    for line in content.splitlines():
        if line.lower().startswith("**subject:**"):
            return line.split("**Subject:**")[-1].strip()
    return "No Subject"


def claude_reason(email_content: str, filename: str) -> str:
    """
    Call Claude API to analyze the email and generate an action plan.
    Falls back to rule-based plan if no API key.
    """
    priority = detect_priority(email_content)
    client   = extract_client(email_content)
    subject  = extract_subject(email_content)

    if DRY_RUN:
        # Rule-based fallback plan (no Claude API needed)
        print(f"  [DRY-RUN] Generating rule-based plan for: {filename}")
        return generate_rule_based_plan(filename, email_content, priority, client, subject)

    try:
        import anthropic
        client_api = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        prompt = f"""You are AutoOps AI, an email operations assistant for a small business.

Analyze this incoming email and create a detailed action plan.

EMAIL:
{email_content}

Create a Plan.md with:
1. What action is needed (reply, call, invoice, meeting, etc.)
2. Urgency level and why
3. Step-by-step response plan
4. Draft reply outline

Format as markdown with clear sections. Be concise and business-focused."""

        message = client_api.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    except Exception as e:
        log.error(f"Claude API error: {e}")
        print(f"  [!] Claude API failed ({e}) — using rule-based plan")
        return generate_rule_based_plan(filename, email_content, priority, client, subject)


def generate_rule_based_plan(filename, content, priority, client, subject) -> str:
    """Fallback: generate plan using keyword logic."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    steps = []

    text = content.lower()
    if "invoice" in text or "payment" in text:
        steps = [
            "1. Confirm invoice number and amount",
            "2. Check payment status in accounting system",
            "3. Reply with payment confirmation or next steps",
            "4. CC accounts team if overdue",
        ]
        action = "Process invoice/payment request"
    elif "meeting" in text or "schedule" in text:
        steps = [
            "1. Check calendar availability",
            "2. Propose 2-3 time slots",
            "3. Send calendar invite after confirmation",
            "4. Prepare meeting agenda",
        ]
        action = "Schedule meeting"
    elif "urgent" in text or "asap" in text:
        steps = [
            "1. Acknowledge receipt immediately",
            "2. Assess what is specifically needed",
            "3. Escalate to relevant team member",
            "4. Provide ETA for resolution",
        ]
        action = "Handle urgent request"
    else:
        steps = [
            "1. Read and understand the full request",
            "2. Identify the appropriate response",
            "3. Draft a professional reply",
            "4. Review before sending",
        ]
        action = "General correspondence"

    return f"""# Plan: {subject}

**Created:** {now}
**Source:** {filename}
**Client:** {client}
**Priority:** {priority}
**Action:** {action}
**Status:** Pending Approval

## Analysis
Email from {client} regarding: "{subject}"
Priority detected: {priority}

## Action Steps
{chr(10).join(steps)}

## Draft Reply Outline
- Acknowledge: Thank the client for reaching out
- Address: Directly respond to their specific request
- Next steps: Provide clear timeline and next actions
- Close: Professional sign-off

## Auto-Generated
This plan was created by AutoOps AI reasoning loop.
Human review required before executing.
"""


def create_draft_reply(email_content: str, filename: str, plan: str) -> str:
    """Create a draft reply for Pending_Approval."""
    client  = extract_client(email_content)
    subject = extract_subject(email_content)
    priority = detect_priority(email_content)

    first_name = client.split("@")[0].split(".")[0].title() if "@" in client else "there"

    return f"""**To:** {client}
**Subject:** Re: {subject}
**Priority:** {priority}
**Client:** {client}

## Body

Dear {first_name},

Thank you for reaching out to us. We have received your message regarding "{subject}" and are reviewing it promptly.

We will get back to you with a complete response shortly.

Best regards,
AutoOps AI Assistant
"""


def process_email(filepath: Path) -> bool:
    """Process one email file: reason → plan → draft → pending approval."""
    filename = filepath.name
    print(f"\n[→] Processing: {filename}")
    log.info(f"Processing: {filename}")

    try:
        content = filepath.read_text(encoding="utf-8")
        priority = detect_priority(content)
        client   = extract_client(content)
        print(f"  Priority: {priority} | Client: {client}")

        # Step 1: Claude reasoning → Plan.md
        print(f"  Reasoning with Claude...")
        plan_content = claude_reason(content, filename)

        plan_name = f"plan_{filepath.stem}.md"
        plan_path = PLANS / plan_name
        plan_path.write_text(plan_content, encoding="utf-8")
        print(f"  ✅ Plan saved: Plans/{plan_name}")
        log.info(f"Plan created: {plan_name}")

        # Step 2: Create draft reply → Pending_Approval
        draft = create_draft_reply(content, filename, plan_content)
        draft_path = PENDING / filename
        draft_path.write_text(draft, encoding="utf-8")
        print(f"  ✅ Draft saved: Pending_Approval/{filename}")
        log.info(f"Draft ready for approval: {filename}")

        mark_processed(filename)
        return True

    except Exception as e:
        log.error(f"Error processing {filename}: {e}")
        print(f"  [ERROR] {e}")
        return False


def run_once():
    """Process all unprocessed files in Needs_Action."""
    files = [f for f in NEEDS_ACTION.glob("*.md") if not f.name.startswith(".")]
    processed = get_processed()
    pending   = [f for f in files if f.name not in processed]

    print(f"\n{'='*50}")
    print(f"AutoOps AI — Reasoning Loop")
    print(f"{'='*50}")
    print(f"Mode: {'DRY-RUN (rule-based)' if DRY_RUN else 'LIVE (Claude API)'}")
    print(f"Files in Needs_Action : {len(files)}")
    print(f"Already processed     : {len(processed)}")
    print(f"To process now        : {len(pending)}")
    print(f"{'='*50}")

    if not pending:
        print("Nothing new to process.")
        return 0

    success = 0
    for filepath in pending:
        if process_email(filepath):
            success += 1

    print(f"\n✅ Done: {success}/{len(pending)} processed")
    print(f"Check Plans/ for generated plans")
    print(f"Check Pending_Approval/ for draft replies awaiting approval")
    log.info(f"Reasoning loop complete: {success}/{len(pending)} processed")
    return success


def run_watch(interval: int = 60):
    """Continuous watch mode — check every N seconds."""
    print(f"Watching Needs_Action/ every {interval}s... (Ctrl+C to stop)")
    log.info(f"Reasoning loop watch mode started (interval={interval}s)")
    while True:
        try:
            run_once()
            time.sleep(interval)
        except KeyboardInterrupt:
            print("\nReasonning loop stopped.")
            break
        except Exception as e:
            log.error(f"Watch loop error: {e}")
            time.sleep(interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AutoOps AI Reasoning Loop")
    parser.add_argument("--watch", action="store_true", help="Continuous watch mode")
    parser.add_argument("--interval", type=int, default=60, help="Watch interval in seconds")
    args = parser.parse_args()

    if args.watch:
        run_watch(args.interval)
    else:
        run_once()
