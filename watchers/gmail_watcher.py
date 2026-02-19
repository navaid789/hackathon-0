"""
Gmail Watcher
-------------
Har 60 second mein Gmail check karta hai.
Naye unread emails ko Needs_Action folder mein save karta hai.

Setup:
1. Google Cloud Console se credentials.json download karo
2. Pehli baar run karo -> browser mein login karega -> token.json ban jaega
3. Phir automatic chalega
"""

import os
import time
import base64
import json
from pathlib import Path
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# --- Config ---
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
VAULT = Path("AI_Employee_Vault")
NEEDS = VAULT / "Needs_Action"
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"
SEEN_FILE = "watchers/seen_emails.json"
CHECK_INTERVAL = 60  # seconds


def get_gmail_service():
    """Gmail API se connect karo."""
    creds = None

    if Path(TOKEN_FILE).exists():
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def load_seen():
    """Pehle dekhe gaye email IDs load karo."""
    if Path(SEEN_FILE).exists():
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    return set()


def save_seen(seen):
    """Dekhe gaye email IDs save karo."""
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)


def get_email_body(msg):
    """Email ka text body nikalo."""
    try:
        parts = msg["payload"].get("parts", [])
        for part in parts:
            if part["mimeType"] == "text/plain":
                data = part["body"].get("data", "")
                return base64.urlsafe_b64decode(data).decode("utf-8")
        # Single part email
        data = msg["payload"]["body"].get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8")
    except Exception:
        pass
    return "(Body read nahi ho saka)"


def save_email_as_task(msg_id, headers, body):
    """Email ko Needs_Action mein .md file ke roop mein save karo."""
    subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
    sender  = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
    date    = next((h["value"] for h in headers if h["name"] == "Date"), "Unknown")

    filename = f"EMAIL_{msg_id[:8]}.md"
    filepath = NEEDS / filename

    content = f"""# Email Task

**From:** {sender}
**Date:** {date}
**Subject:** {subject}

## Message
{body.strip()}

---
**Status:** Needs Action
**Detected:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""

    filepath.write_text(content, encoding="utf-8")
    print(f"[+] Saved: {filename} | Subject: {subject}")


def check_emails(service, seen):
    """Naye unread emails dhundo."""
    results = service.users().messages().list(
        userId="me",
        labelIds=["INBOX", "UNREAD"],
        maxResults=10
    ).execute()

    messages = results.get("messages", [])
    new_count = 0

    for m in messages:
        msg_id = m["id"]
        if msg_id in seen:
            continue

        msg = service.users().messages().get(
            userId="me", id=msg_id, format="full"
        ).execute()

        headers = msg["payload"].get("headers", [])
        body    = get_email_body(msg)

        save_email_as_task(msg_id, headers, body)
        seen.add(msg_id)
        new_count += 1

    return new_count


def main():
    print("Gmail Watcher start ho gaya...")
    print(f"Har {CHECK_INTERVAL} seconds mein check karega.\n")

    service = get_gmail_service()
    seen    = load_seen()

    while True:
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Emails check kar raha hoon...")
            count = check_emails(service, seen)
            save_seen(seen)

            if count:
                print(f"  -> {count} naye email(s) Needs_Action mein save ho gaye!\n")
            else:
                print("  -> Koi naya email nahi mila.\n")

        except Exception as e:
            print(f"[ERROR] {e}\n")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
