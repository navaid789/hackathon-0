"""
AutoOps AI — Gmail Watcher
----------------------------
Checks Gmail every 60 seconds for new unread emails.
Saves each email as a .md task file in Needs_Action/.

Features:
  - Dry-run mode if credentials.json not found
  - Crash protection — never stops on single email error
  - Deduplication via seen_emails.json
  - Full logging to system.log
  - Graceful token refresh

Setup:
  1. Google Cloud Console → APIs & Services → Credentials
  2. Create OAuth 2.0 Client ID (Desktop App)
  3. Download JSON → rename to credentials.json
  4. Place in project root: /mnt/d/hackathon 0/credentials.json
  5. First run → browser opens for Gmail login → token.json saved
  6. All future runs are automatic

Run:
    python watchers/gmail_watcher.py
"""

import os
import time
import base64
import json
import logging
from pathlib import Path
from datetime import datetime

# ─── Config ───────────────────────────────────────────────────────────────────
VAULT            = Path("AI_Employee_Vault")
NEEDS            = VAULT / "Needs_Action"
LOGS             = VAULT / "Logs"
CREDENTIALS_FILE = Path("credentials.json")
TOKEN_FILE       = Path("token.json")
SEEN_FILE        = Path("watchers/seen_emails.json")
SCOPES           = ["https://www.googleapis.com/auth/gmail.readonly"]
CHECK_INTERVAL   = 60  # seconds
DRY_RUN          = not CREDENTIALS_FILE.exists()

# ─── Logging ──────────────────────────────────────────────────────────────────
LOGS.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=str(LOGS / "system.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
log = logging.getLogger(__name__)


# ─── Dry-Run Simulation ───────────────────────────────────────────────────────

def simulate_email_check(seen: set) -> int:
    """Simulate email detection without Gmail API."""
    print(f"  [DRY-RUN] Simulating Gmail check...")
    print(f"  Add credentials.json to project root for live Gmail.")
    log.info("DRY-RUN: Gmail check simulated (no credentials.json)")
    return 0


# ─── Gmail API ───────────────────────────────────────────────────────────────

def get_gmail_service():
    """Connect to Gmail API with OAuth2. Auto-refreshes token."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        raise RuntimeError(
            "Google API libraries not installed.\n"
            "Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
        )

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            log.info("Gmail token refreshed.")
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
            log.info("Gmail OAuth flow completed — new token saved.")
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


# ─── Seen Email Tracking ──────────────────────────────────────────────────────

def load_seen() -> set:
    """Load previously seen email IDs to avoid duplicates."""
    try:
        if SEEN_FILE.exists():
            return set(json.loads(SEEN_FILE.read_text()))
    except Exception as e:
        log.warning(f"Could not load seen_emails.json: {e}")
    return set()


def save_seen(seen: set):
    """Save seen email IDs."""
    try:
        SEEN_FILE.write_text(json.dumps(list(seen)))
    except Exception as e:
        log.warning(f"Could not save seen_emails.json: {e}")


# ─── Email Processing ─────────────────────────────────────────────────────────

def get_email_body(msg: dict) -> str:
    """Extract plain text body from Gmail message."""
    try:
        payload = msg.get("payload", {})
        parts   = payload.get("parts", [])

        # Multi-part email
        for part in parts:
            if part.get("mimeType") == "text/plain":
                data = part["body"].get("data", "")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

        # Single part email
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    except Exception as e:
        log.warning(f"Could not decode email body: {e}")

    return "(Email body could not be read)"


def save_email_as_task(msg_id: str, headers: list, body: str):
    """Save email as a Markdown task file in Needs_Action/."""
    subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
    sender  = next((h["value"] for h in headers if h["name"] == "From"),    "Unknown Sender")
    date    = next((h["value"] for h in headers if h["name"] == "Date"),    "Unknown Date")

    filename = f"EMAIL_{msg_id[:8]}.md"
    filepath = NEEDS / filename

    # Detect priority from subject/body keywords
    combined = (subject + " " + body).lower()
    if any(w in combined for w in ["urgent", "asap", "immediately", "critical", "overdue", "invoice", "payment"]):
        priority = "HIGH"
    elif any(w in combined for w in ["meeting", "schedule", "follow-up", "proposal", "contract"]):
        priority = "MEDIUM"
    else:
        priority = "LOW"

    content = f"""# Email Task

**From:** {sender}
**Subject:** {subject}
**Date:** {date}
**Priority:** {priority}
**Detected:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Status:** Needs Action

## Message

{body.strip()[:3000]}

---
*Saved by Gmail Watcher — AutoOps AI*
"""
    filepath.write_text(content, encoding="utf-8")
    log.info(f"Email saved: {filename} | From: {sender} | Priority: {priority}")
    print(f"  [+] Saved: {filename} | Priority: {priority} | From: {sender[:40]}")


def check_emails(service, seen: set) -> int:
    """Fetch new unread emails. Returns count of new emails saved."""
    try:
        results  = service.users().messages().list(
            userId="me",
            labelIds=["INBOX", "UNREAD"],
            maxResults=10,
        ).execute()
        messages = results.get("messages", [])
    except Exception as e:
        log.error(f"Gmail API list error: {e}")
        print(f"  [ERROR] Could not fetch emails: {e}")
        return 0

    new_count = 0
    for m in messages:
        msg_id = m["id"]
        if msg_id in seen:
            continue

        try:
            msg     = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
            headers = msg["payload"].get("headers", [])
            body    = get_email_body(msg)
            save_email_as_task(msg_id, headers, body)
            seen.add(msg_id)
            new_count += 1

        except Exception as e:
            log.error(f"Error processing email {msg_id}: {e}")
            print(f"  [ERROR] Email {msg_id[:8]}: {e} — skipping")
            seen.add(msg_id)  # Mark as seen to avoid retry loop

    return new_count


# ─── Main Loop ────────────────────────────────────────────────────────────────

def main():
    print("=" * 45)
    print("AutoOps AI — Gmail Watcher")
    print("=" * 45)
    print(f"Mode:     {'DRY-RUN (no credentials.json)' if DRY_RUN else 'LIVE (Gmail API)'}")
    print(f"Interval: every {CHECK_INTERVAL}s")
    print(f"Target:   {NEEDS.resolve()}")
    print("Ctrl+C to stop.\n")

    log.info(f"Gmail Watcher started (mode={'DRY-RUN' if DRY_RUN else 'LIVE'})")

    # Ensure folders exist
    NEEDS.mkdir(parents=True, exist_ok=True)

    service = None
    if not DRY_RUN:
        try:
            service = get_gmail_service()
            log.info("Gmail API connected successfully.")
            print("✅ Gmail API connected.\n")
        except Exception as e:
            log.error(f"Gmail connect failed: {e}")
            print(f"[!] Gmail connect failed: {e}")
            print("[!] Switching to DRY-RUN mode.\n")

    seen = load_seen()

    while True:
        try:
            ts = datetime.now().strftime("%H:%M:%S")
            print(f"[{ts}] Checking emails...")

            if service:
                count = check_emails(service, seen)
                save_seen(seen)
                if count:
                    print(f"  → {count} new email(s) saved to Needs_Action/\n")
                else:
                    print("  → No new emails.\n")
            else:
                simulate_email_check(seen)

        except KeyboardInterrupt:
            raise

        except Exception as e:
            # Crash protection — log and continue
            log.error(f"Watch loop error (recovered): {e}")
            print(f"[ERROR] Recovered from crash: {e}")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("Gmail Watcher stopped by user.")
        print("\n[✅] Gmail Watcher stopped. Khuda Hafiz!")
