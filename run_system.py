"""
AI Employee — Master Runner
----------------------------
Ek command se poora system start karo:
    python run_system.py
"""

import subprocess
import sys
from datetime import datetime

scripts = [
    "filesystem_watcher.py",
    "watchers/gmail_watcher.py",
    "watchers/approval_watcher.py",
    "orchestration/scheduler.py",
    "dashboard_ui.py",
]

processes = []

print("=" * 40)
print("   AI EMPLOYEE SYSTEM STARTING...")
print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 40)

for script in scripts:
    p = subprocess.Popen([sys.executable, script])
    processes.append(p)
    print(f"  ✓ Started: {script} (PID: {p.pid})")

print()
print("  Dashboard (Flask)  → http://localhost:5000
  Dashboard (React)  → http://localhost:5173
  API Docs           → http://localhost:8000/docs")
print("  Ctrl+C    → Sab band karo")
print("=" * 40)

try:
    for p in processes:
        p.wait()
except KeyboardInterrupt:
    print("\nSystem band ho raha hai...")
    for p in processes:
        p.terminate()
    print("Khuda Hafiz!")
