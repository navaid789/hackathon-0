import os
import time
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
VAULT = Path("AI_Employee_Vault")
NEEDS = VAULT / "Needs_Action"

def authenticate():
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    return build('gmail', 'v1', credentials=creds)

service = authenticate()
seen = set()

while True:
    results = service.users().messages().list(
        userId='me',
        q='is:unread'
    ).execute()

    messages = results.get('messages', [])

    for msg in messages:
        if msg['id'] in seen:
            continue

        email = service.users().messages().get(
            userId='me', id=msg['id']
        ).execute()

        snippet = email.get('snippet', '')

        file = NEEDS / f"EMAIL_{msg['id']}.md"
        file.write_text(f"# New Email\n\n{snippet}")

        seen.add(msg['id'])
        print("Email saved:", file.name)

    time.sleep(60)
