import time
from pathlib import Path
import shutil

VAULT = Path("AI_Employee_Vault")
INBOX = VAULT / "Inbox"
NEEDS = VAULT / "Needs_Action"

while True:
    for file in INBOX.glob("*"):
        shutil.move(file, NEEDS / file.name)
        print(f"Moved: {file.name}")
    time.sleep(5)
