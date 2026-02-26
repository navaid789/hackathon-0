"""
AutoOps AI — Filesystem Watcher
---------------------------------
Monitors AI_Employee_Vault/Inbox/ every 5 seconds.
Moves any new files to Needs_Action/ for processing.

Features:
  - Crash protection with try/except
  - Full logging to system.log
  - Graceful degradation (missing folders auto-created)
  - Skips hidden files and temp files
  - Handles permission errors

Run:
    python watchers/filesystem_watcher.py
"""

import time
import shutil
import logging
from pathlib import Path
from datetime import datetime

# ─── Config ───────────────────────────────────────────────────────────────────
VAULT = Path("AI_Employee_Vault")
INBOX = VAULT / "Inbox"
NEEDS = VAULT / "Needs_Action"
CHECK_INTERVAL = 5  # seconds

# ─── Logging ──────────────────────────────────────────────────────────────────
LOGS = VAULT / "Logs"
LOGS.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=str(LOGS / "system.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
log = logging.getLogger(__name__)


def ensure_folders():
    """Create required folders if missing (graceful degradation)."""
    for folder in [INBOX, NEEDS]:
        if not folder.exists():
            folder.mkdir(parents=True, exist_ok=True)
            log.info(f"Created missing folder: {folder}")
            print(f"[!] Created folder: {folder}")


def should_skip(file: Path) -> bool:
    """Skip hidden files, temp files, and non-content files."""
    name = file.name
    return (
        name.startswith(".")       # hidden files
        or name.startswith("~")    # temp files
        or name.endswith(".tmp")   # temp files
        or name.endswith(".part")  # partial downloads
        or not file.is_file()      # directories
    )


def move_file(file: Path) -> bool:
    """Move one file from Inbox to Needs_Action. Returns True on success."""
    dst = NEEDS / file.name
    try:
        # If destination already exists, add timestamp suffix
        if dst.exists():
            stem = file.stem
            suffix = file.suffix
            ts = datetime.now().strftime("%H%M%S")
            dst = NEEDS / f"{stem}_{ts}{suffix}"

        shutil.move(str(file), str(dst))
        log.info(f"Moved to Needs_Action: {file.name}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Moved: {file.name} → Needs_Action/")
        return True

    except PermissionError as e:
        log.warning(f"Permission denied moving {file.name}: {e}")
        print(f"[!] Permission error: {file.name} — skipping")
        return False
    except Exception as e:
        log.error(f"Failed to move {file.name}: {e}")
        print(f"[ERROR] Could not move {file.name}: {e}")
        return False


def main():
    print("=" * 45)
    print("AutoOps AI — Filesystem Watcher")
    print("=" * 45)
    print(f"Watching: {INBOX.resolve()}")
    print(f"Target:   {NEEDS.resolve()}")
    print(f"Interval: every {CHECK_INTERVAL}s")
    print("Ctrl+C to stop.\n")

    log.info("Filesystem Watcher started.")
    ensure_folders()

    while True:
        try:
            files = [f for f in INBOX.iterdir() if not should_skip(f)]

            if files:
                moved = sum(1 for f in files if move_file(f))
                if moved:
                    print(f"  → {moved} file(s) moved to Needs_Action/\n")
            else:
                # Silent when idle — no spam
                pass

        except FileNotFoundError:
            # Inbox folder deleted — recreate it
            log.warning("Inbox folder missing — recreating")
            ensure_folders()

        except PermissionError as e:
            log.error(f"Permission error on Inbox scan: {e}")
            print(f"[!] Permission error scanning Inbox: {e}")

        except Exception as e:
            log.error(f"Unexpected error in watch loop: {e}")
            print(f"[ERROR] Watch loop error: {e}")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("Filesystem Watcher stopped by user.")
        print("\n[✅] Filesystem Watcher stopped. Khuda Hafiz!")
