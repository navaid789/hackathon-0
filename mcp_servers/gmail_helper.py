"""
Gmail Helper for MCP Server
Called by gmail_server.js to perform Gmail API operations
Usage: python3 gmail_helper.py '{"action": "check_unread", "max_results": 5}'
"""

import sys
import json
import base64
from pathlib import Path
from email.mime.text import MIMEText

VAULT      = Path("AI_Employee_Vault")
NEEDS      = VAULT / "Needs_Action"
CREDS_FILE = Path("credentials.json")
TOKEN_FILE = Path("token_gmail_mcp.json")
SCOPES     = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]


def get_service():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def check_unread(max_results=10):
    service = get_service()
    results = service.users().messages().list(
        userId="me",
        labelIds=["UNREAD", "INBOX"],
        maxResults=max_results,
    ).execute()

    messages = results.get("messages", [])
    saved_files = []

    for msg in messages:
        msg_data = service.users().messages().get(
            userId="me", id=msg["id"], format="full"
        ).execute()

        headers = {h["name"]: h["value"] for h in msg_data["payload"].get("headers", [])}
        from_addr = headers.get("From", "unknown@unknown.com")
        subject   = headers.get("Subject", "No Subject")
        date      = headers.get("Date", "")

        # Extract body
        body = ""
        payload = msg_data.get("payload", {})
        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain":
                    data = part["body"].get("data", "")
                    if data:
                        body = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                        break
        elif payload.get("body", {}).get("data"):
            body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

        # Save as markdown
        safe_id = msg["id"][:8]
        filename = f"EMAIL_{safe_id}.md"
        content  = f"**From:** {from_addr}\n**Subject:** {subject}\n**Date:** {date}\n\n{body[:2000]}"
        (NEEDS / filename).write_text(content, encoding="utf-8")
        saved_files.append(filename)

        # Mark as read
        service.users().messages().modify(
            userId="me", id=msg["id"],
            body={"removeLabelIds": ["UNREAD"]}
        ).execute()

    return {"count": len(saved_files), "files": saved_files}


def send_email(to, subject, body):
    service = get_service()
    message = MIMEText(body)
    message["to"]      = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    result = service.users().messages().send(
        userId="me", body={"raw": raw}
    ).execute()
    return {"message_id": result.get("id"), "status": "sent"}


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No arguments provided"}))
        sys.exit(1)

    try:
        args = json.loads(sys.argv[1])
        action = args.pop("action", "")

        if action == "check_unread":
            result = check_unread(args.get("max_results", 10))
        elif action == "send":
            result = send_email(args["to"], args["subject"], args["body"])
        else:
            result = {"error": f"Unknown action: {action}"}

        print(json.dumps(result))

    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
