"""
AI Employee Orchestrator
------------------------
Ek command se saare watchers ek saath chalata hai.

Run karo:
    cd "/mnt/d/hackathon 0"
    python orchestration/orchestrator.py
"""

import subprocess
import time
import sys
from pathlib import Path
from datetime import datetime

WATCHERS = [
    {
        "name": "Filesystem Watcher",
        "script": "filesystem_watcher.py",
        "color": "\033[94m",   # blue
    },
    {
        "name": "Gmail Watcher",
        "script": "watchers/gmail_watcher.py",
        "color": "\033[93m",   # yellow
    },
    {
        "name": "Approval Watcher",
        "script": "watchers/approval_watcher.py",
        "color": "\033[92m",   # green
    },
    {
        "name": "LinkedIn Watcher",
        "script": "watchers/linkedin_watcher.py --watch",
        "color": "\033[96m",   # cyan
    },
    {
        "name": "Reasoning Loop",
        "script": "orchestration/reasoning_loop.py --watch",
        "color": "\033[95m",   # magenta
    },
]

RESET = "\033[0m"
BOLD  = "\033[1m"

processes = []


def log(msg):
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] {msg}")


def start_watchers():
    for w in WATCHERS:
        script = Path(w["script"])
        if not script.exists():
            log(f"[SKIP] {w['name']} — script nahi mili: {script}")
            continue

        # Support args in script string (e.g. "script.py --watch")
        script_parts = str(w["script"]).split()
        proc = subprocess.Popen(
            [sys.executable] + script_parts,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        processes.append({"name": w["name"], "color": w["color"], "proc": proc})
        log(f"{w['color']}{BOLD}[START]{RESET} {w['name']} (PID: {proc.pid})")


def monitor():
    log(f"{BOLD}AI Employee Orchestrator chal raha hai...{RESET}")
    log(f"Watchers: {len(processes)} active\n")

    try:
        while True:
            for w in processes:
                proc = w["proc"]
                name = w["name"]
                color = w["color"]

                # Output print karo
                line = proc.stdout.readline()
                if line:
                    print(f"{color}[{name}]{RESET} {line.strip()}")

                # Agar crash ho gaya to restart karo
                if proc.poll() is not None:
                    log(f"[WARN] {name} band ho gaya — restart kar raha hoon...")
                    new_proc = subprocess.Popen(
                        [sys.executable, proc.args[1]],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1
                    )
                    w["proc"] = new_proc
                    log(f"{color}[RESTART]{RESET} {name} (PID: {new_proc.pid})")

            time.sleep(0.1)

    except KeyboardInterrupt:
        log("\nOrchestrator band ho raha hai...")
        for w in processes:
            w["proc"].terminate()
        log("Saare watchers band ho gaye. Khuda Hafiz!")


if __name__ == "__main__":
    start_watchers()
    monitor()
