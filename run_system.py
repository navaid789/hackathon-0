"""
AutoOps AI — Master Runner
----------------------------
Ek command se poora system start karo:
    python run_system.py
"""

import subprocess
import sys
from datetime import datetime

scripts = [
    "watchers/filesystem_watcher.py",   # Inbox → Needs_Action
    "watchers/gmail_watcher.py",         # Gmail API monitor
    "watchers/approval_watcher.py",      # Send approved emails
    "orchestration/scheduler.py",        # Daily reports (9am/6pm)
    "dashboard_ui.py",                   # Flask dashboard :5000
]

processes = []

print("=" * 45)
print("   AutoOps AI — SYSTEM STARTING")
print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 45)

for script in scripts:
    try:
        p = subprocess.Popen([sys.executable, script])
        processes.append(p)
        print(f"  OK  {script} (PID: {p.pid})")
    except Exception as e:
        print(f"  FAIL {script} -> {e}")

print()
print("  Flask Dashboard  -> http://localhost:5000")
print("  React Dashboard  -> http://localhost:5173")
print("  API Docs         -> http://localhost:8000/docs")
print()
print("  Ctrl+C -> Sab band karo")
print("=" * 45)

try:
    for p in processes:
        p.wait()
except KeyboardInterrupt:
    print("\nSystem band ho raha hai...")
    for p in processes:
        p.terminate()
    print("Khuda Hafiz!")
