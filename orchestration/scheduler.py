"""
AI Employee Scheduler
---------------------
Automatically kaam karta hai:
- Har subah 9:00 baje → Emails check karo, report banao
- Har 30 min mein → Inbox check karo
- Har raat 6:00 baje → Daily summary Dashboard mein likhо

Run karo:
    cd "/mnt/d/hackathon 0"
    python orchestration/scheduler.py
"""

import schedule
import time
import shutil
from pathlib import Path
from datetime import datetime

VAULT   = Path("AI_Employee_Vault")
INBOX   = VAULT / "Inbox"
NEEDS   = VAULT / "Needs_Action"
DONE    = VAULT / "Done"
LOGS    = VAULT / "Logs"
DASH    = VAULT / "Dashboard.md"


def log(msg):
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] {msg}")


# ─── Jobs ────────────────────────────────────────────────

def check_inbox():
    """Inbox mein files dhundo aur Needs_Action mein move karo."""
    log("Inbox check kar raha hoon...")
    moved = 0
    for file in INBOX.glob("*"):
        shutil.move(str(file), NEEDS / file.name)
        log(f"  Moved: {file.name}")
        moved += 1
    if moved == 0:
        log("  Inbox khali hai.")
    else:
        log(f"  {moved} file(s) Needs_Action mein bhej di.")


def morning_report():
    """Subah ki report banao."""
    log("Morning report bana raha hoon...")

    needs  = list(NEEDS.glob("*.md"))
    done   = list(DONE.glob("*.md"))
    today  = datetime.now().strftime("%Y-%m-%d")

    report = f"""# Morning Report — {today}

**Time:** {datetime.now().strftime('%H:%M')}

## Needs Action
{chr(10).join(f'- {f.name}' for f in needs) or '- Kuch nahi'}

## Done (Total)
{chr(10).join(f'- {f.name}' for f in done) or '- Kuch nahi'}

## Status
- Needs Action: {len(needs)} tasks
- Done: {len(done)} tasks
"""

    report_file = LOGS / f"morning_report_{today}.md"
    report_file.write_text(report, encoding="utf-8")
    log(f"  Report save ho gayi: {report_file.name}")
    update_dashboard(needs, done)


def evening_summary():
    """Raat ko daily summary banao."""
    log("Evening summary bana raha hoon...")

    done  = list(DONE.glob("*.md"))
    today = datetime.now().strftime("%Y-%m-%d")

    summary = f"""# Evening Summary — {today}

**Time:** {datetime.now().strftime('%H:%M')}

## Aaj ka kaam
- Tasks complete hue: {len(done)}

## Done Files
{chr(10).join(f'- {f.name}' for f in done) or '- Kuch nahi'}

Kal phir milenge!
"""

    summary_file = LOGS / f"evening_summary_{today}.md"
    summary_file.write_text(summary, encoding="utf-8")
    log(f"  Summary save ho gayi: {summary_file.name}")


def update_dashboard(needs, done):
    """Dashboard.md update karo."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    content = f"""# AI Employee Dashboard

## Status
Online — Last updated: {now}

## Pending Tasks
{chr(10).join(f'- {f.name}' for f in needs) or '- None'}

## Done (Total)
{chr(10).join(f'- {f.name}' for f in done) or '- None'}

## Recent Activity
- Morning report banaya ({now})
- Scheduler chal raha hai

Yeh tumhara control center hai.
"""
    DASH.write_text(content, encoding="utf-8")
    log("  Dashboard update ho gaya.")


# ─── Schedule ────────────────────────────────────────────

# check_inbox removed — filesystem_watcher.py handles this (no duplicate!)
schedule.every().day.at("09:00").do(morning_report)
schedule.every().day.at("18:00").do(evening_summary)


# ─── Main ────────────────────────────────────────────────

def main():
    log("AI Employee Scheduler shuru ho gaya!")
    log("Schedule:")
    log("  09:00 roz   → Morning report")
    log("  18:00 roz   → Evening summary")
    log("  (Inbox: filesystem_watcher.py handle karta hai)")
    log("Ctrl+C dabao band karne ke liye.\n")

    # Shuru mein ek baar chalao
    morning_report()

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
