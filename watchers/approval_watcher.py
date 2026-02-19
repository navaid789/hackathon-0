"""
Approval Watcher + Gmail Sender
--------------------------------
Approved/ folder check karta hai har 10 seconds mein.
Logging + Crash Protection included.
"""

import time
import base64
import shutil
import logging
from pathlib import Path
from email.mime.text import MIMEText

# ─── Logging Setup ───────────────────────────────────────
logging.basicConfig(
    filename="AI_Employee_Vault/Logs/system.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

APPROVED   = Path("AI_Employee_Vault/Approved")
DONE       = Path("AI_Employee_Vault/Done")
CREDS_FILE = "credentials.json"
TOKEN_FILE = "token_send.json"
SCOPES     = ["https://www.googleapis.com/auth/gmail.send"]


def get_service():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None
    if Path(TOKEN_FILE).exists():
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def parse_md(filepath):
    text = filepath.read_text(encoding="utf-8")
    to, subject, body_lines = "", "", []
    in_body = False
    for line in text.splitlines():
        if line.startswith("**To:**"):
            to = line.replace("**To:**", "").strip()
        elif line.startswith("**Subject:**"):
            subject = line.replace("**Subject:**", "").strip()
        elif line.startswith("## Body"):
            in_body = True
        elif in_body:
            body_lines.append(line)
    return to, subject, "\n".join(body_lines).strip()


def send_email(service, to, subject, body):
    message = MIMEText(body)
    message["to"]      = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()


def main():
    logging.info("Approval Watcher start ho gaya.")
    print("Approval Watcher chal raha hai...")

    # Gmail service — credentials nahi hain to simulation mode
    service = None
    if Path(CREDS_FILE).exists():
        try:
            service = get_service()
            logging.info("Gmail service connected.")
        except Exception as e:
            logging.error(f"Gmail connect nahi hua: {e}")
    else:
        logging.warning("credentials.json nahi mili — simulation mode.")
        print("  [!] credentials.json nahi — dry run mode.")

    # ─── Main Loop with Crash Protection ─────────────────
    while True:
        try:
            for file in APPROVED.glob("*.md"):
                logging.info(f"Approved file mili: {file.name}")
                print(f"\n[+] Approved: {file.name}")

                to, subject, body = parse_md(file)

                if not to or not subject:
                    logging.warning(f"To/Subject missing — skip: {file.name}")
                    print("  [!] To ya Subject missing — skip.")
                    shutil.move(str(file), DONE / file.name)
                    continue

                if service:
                    try:
                        send_email(service, to, subject, body)
                        logging.info(f"Email sent to {to} | Subject: {subject}")
                        print(f"  Email bhej diya → {to}")
                    except Exception as e:
                        logging.error(f"Email send fail: {e}")
                        print(f"  [ERROR] Email send nahi hua: {e}")
                else:
                    logging.info(f"[DRY RUN] Email simulate: {to} | {subject}")
                    print(f"  [DRY RUN] Email simulate → {to}")

                shutil.move(str(file), DONE / file.name)
                logging.info(f"Done mein move kiya: {file.name}")
                print(f"  Done/ mein move kar diya.")

        except Exception as e:
            logging.error(f"Crash prevented: {e}")
            print(f"[ERROR] Crash roka gaya: {e}")

        time.sleep(10)


if __name__ == "__main__":
    main()
