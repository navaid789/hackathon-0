"""
AutoOps AI — Ralph Wiggum Loop
---------------------------------
Autonomous multi-step task completion agent.
Named after Ralph Wiggum's ability to "just do things" step by step.

The loop:
  1. Observe  — check all vault folders for pending work
  2. Plan     — decide what to do next (priority order)
  3. Act      — execute the action (reason, draft, approve, post)
  4. Verify   — confirm action completed
  5. Log      — record everything
  6. Repeat   — until no more work or max_cycles reached

Run:
    python orchestration/ralph_loop.py              # run 1 cycle
    python orchestration/ralph_loop.py --cycles 5   # run 5 cycles
    python orchestration/ralph_loop.py --watch       # run every 5 minutes
"""

import os
import sys
import time
import shutil
import logging
import argparse
from pathlib import Path
from datetime import datetime

# ─── Config ───────────────────────────────────────────────────────────────────
VAULT   = Path("AI_Employee_Vault")
INBOX   = VAULT / "Inbox"
NEEDS   = VAULT / "Needs_Action"
PENDING = VAULT / "Pending_Approval"
APPROVED = VAULT / "Approved"
DONE    = VAULT / "Done"
PLANS   = VAULT / "Plans"
LOGS    = VAULT / "Logs"

RALPH_LOG = LOGS / "ralph_loop.log"
MAX_CYCLES_DEFAULT = 10
WATCH_INTERVAL = 300  # 5 minutes

logging.basicConfig(
    filename=str(RALPH_LOG),
    level=logging.INFO,
    format="%(asctime)s - [RALPH] %(levelname)s - %(message)s",
)
log = logging.getLogger("ralph")


def ts():
    return datetime.now().strftime("%H:%M:%S")


def detect_priority(content: str) -> int:
    """Return priority score: 3=HIGH, 2=MEDIUM, 1=LOW."""
    text = content.lower()
    if any(w in text for w in ["urgent", "asap", "immediately", "critical", "overdue", "invoice", "payment"]):
        return 3
    if any(w in text for w in ["meeting", "schedule", "follow-up", "proposal", "contract", "review"]):
        return 2
    return 1


def extract_client(content: str) -> str:
    for line in content.splitlines():
        if "**from:**" in line.lower():
            return line.split(":**")[-1].strip()
    return "Unknown"


def extract_subject(content: str) -> str:
    for line in content.splitlines():
        if "**subject:**" in line.lower():
            return line.split(":**")[-1].strip()
    return "No Subject"


# ─── Observe ──────────────────────────────────────────────────────────────────

def observe() -> dict:
    """Step 1: Observe current state of all vault folders."""
    state = {
        "inbox":    sorted(INBOX.glob("*.md"),    key=lambda f: f.stat().st_mtime, reverse=True),
        "needs":    sorted(NEEDS.glob("*.md"),    key=lambda f: f.stat().st_mtime, reverse=True),
        "pending":  sorted(PENDING.glob("*.md"),  key=lambda f: f.stat().st_mtime, reverse=True),
        "approved": sorted(APPROVED.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True),
        "done":     list(DONE.glob("*.md")),
    }
    return state


# ─── Plan ─────────────────────────────────────────────────────────────────────

def plan(state: dict) -> list:
    """Step 2: Create ordered action list based on current state."""
    actions = []

    # Priority 1: Move inbox → needs_action
    for f in state["inbox"]:
        actions.append({"priority": 10, "action": "move_inbox", "file": f})

    # Priority 2: Process needs_action → plans + pending
    # Load processed files to avoid duplicates
    processed_file = LOGS / "reasoning_processed.txt"
    processed = set(processed_file.read_text().splitlines()) if processed_file.exists() else set()

    for f in state["needs"]:
        if f.name not in processed:
            content = f.read_text(encoding="utf-8", errors="replace")
            p = detect_priority(content)
            actions.append({"priority": p + 5, "action": "reason_and_draft", "file": f})

    # Priority 3: Auto-approve LOW priority pending items (if enabled)
    # Note: HIGH and MEDIUM always require human — only LOW is auto-approved
    for f in state["pending"]:
        content = f.read_text(encoding="utf-8", errors="replace")
        p = detect_priority(content)
        if p == 1:  # LOW priority only
            actions.append({"priority": 1, "action": "auto_approve_low", "file": f})

    # Sort by priority descending
    actions.sort(key=lambda x: x["priority"], reverse=True)
    return actions


# ─── Act ──────────────────────────────────────────────────────────────────────

def act_move_inbox(filepath: Path) -> str:
    """Move file from Inbox to Needs_Action."""
    dst = NEEDS / filepath.name
    shutil.move(str(filepath), dst)
    msg = f"Moved {filepath.name}: Inbox → Needs_Action"
    log.info(msg)
    return msg


def act_reason_and_draft(filepath: Path) -> str:
    """Run reasoning loop on a single file — create plan + draft reply."""
    content = filepath.read_text(encoding="utf-8", errors="replace")
    client  = extract_client(content)
    subject = extract_subject(content)
    p_score = detect_priority(content)
    p_label = {3: "HIGH", 2: "MEDIUM", 1: "LOW"}[p_score]

    # Detect action type
    text = content.lower()
    if "invoice" in text or "payment" in text:
        action_type = "invoice"
        steps = ["Confirm invoice details", "Check payment status", "Reply with confirmation", "CC accounts team if overdue"]
    elif "meeting" in text or "schedule" in text:
        action_type = "meeting"
        steps = ["Check calendar availability", "Propose 2-3 time slots", "Send calendar invite", "Prepare agenda"]
    else:
        action_type = "general"
        steps = ["Read and understand request", "Draft professional response", "Review tone and accuracy", "Submit for approval"]

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Save plan
    plan_content = f"""# Plan: {subject}

**Created:** {now} (by Ralph Wiggum Loop)
**Source:** {filepath.name}
**Client:** {client}
**Priority:** {p_label}
**Action Type:** {action_type}
**Status:** Pending Approval

## Analysis
Email from {client} regarding "{subject}".
Detected priority: {p_label} — action type: {action_type}.

## Action Steps
{chr(10).join(f'{i+1}. {s}' for i, s in enumerate(steps))}

## Draft Outline
- Acknowledge: Thank client for reaching out
- Address: Directly respond to "{subject}"
- Next steps: Clear timeline and action items
- Close: Professional sign-off

*Auto-generated by Ralph Wiggum Loop — human review required*
"""
    plan_path = PLANS / f"plan_{filepath.stem}.md"
    plan_path.write_text(plan_content, encoding="utf-8")

    # Save draft reply to Pending_Approval
    first_name = client.split("@")[0].replace(".", " ").title() if "@" in client else "there"
    draft = f"""**To:** {client}
**Subject:** Re: {subject}
**Priority:** {p_label}
**Client:** {client}

## Body

Dear {first_name},

Thank you for reaching out. We have received your message and are reviewing it promptly.

{"This is flagged as HIGH priority and will receive immediate attention." if p_label == "HIGH" else "We will respond with a complete answer shortly."}

Best regards,
AutoOps AI Assistant

---
*Draft by Ralph Wiggum Loop — awaiting human approval before sending*
"""
    pending_path = PENDING / filepath.name
    pending_path.write_text(draft, encoding="utf-8")

    # Mark as processed
    processed_file = LOGS / "reasoning_processed.txt"
    with open(processed_file, "a") as pf:
        pf.write(filepath.name + "\n")

    msg = f"Reasoned + drafted {filepath.name} [{p_label}] → Plans/ + Pending_Approval/"
    log.info(msg)
    return msg


def act_auto_approve_low(filepath: Path) -> str:
    """Auto-approve LOW priority items (no human needed for newsletters/FYIs)."""
    content = filepath.read_text(encoding="utf-8", errors="replace")
    subject = extract_subject(content)

    # Move to Approved
    dst = APPROVED / filepath.name
    shutil.move(str(filepath), dst)

    # Log it
    log_line = f"{datetime.now().isoformat()} - AUTO-APPROVED (LOW): {filepath.name}\n"
    with open(LOGS / "system.log", "a") as lf:
        lf.write(log_line)

    msg = f"Auto-approved LOW priority: {filepath.name} ({subject}) → Approved/"
    log.info(msg)
    return msg


# ─── Verify ───────────────────────────────────────────────────────────────────

def verify(action: dict, result: str) -> bool:
    """Step 4: Verify action completed successfully."""
    filepath = action["file"]
    action_type = action["action"]

    if action_type == "move_inbox":
        return (NEEDS / filepath.name).exists()
    elif action_type == "reason_and_draft":
        return (PLANS / f"plan_{filepath.stem}.md").exists() and (PENDING / filepath.name).exists()
    elif action_type == "auto_approve_low":
        return (APPROVED / filepath.name).exists()
    return True


# ─── Update Dashboard ─────────────────────────────────────────────────────────

def update_dashboard_status():
    """Quick dashboard update after each cycle."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    counts = {
        "Inbox": len(list(INBOX.glob("*.md"))),
        "Needs_Action": len(list(NEEDS.glob("*.md"))),
        "Pending_Approval": len(list(PENDING.glob("*.md"))),
        "Approved": len(list(APPROVED.glob("*.md"))),
        "Done": len(list(DONE.glob("*.md"))),
    }
    summary = " | ".join(f"{k}: {v}" for k, v in counts.items())
    log.info(f"Cycle complete — {summary}")


# ─── One Cycle ────────────────────────────────────────────────────────────────

def run_cycle(cycle_num: int) -> int:
    """Run one full Observe → Plan → Act → Verify cycle. Returns actions taken."""
    print(f"\n{'─'*50}")
    print(f"[{ts()}] Ralph Loop — Cycle {cycle_num}")

    state   = observe()
    actions = plan(state)

    print(f"  Observe: inbox={len(state['inbox'])} needs={len(state['needs'])} pending={len(state['pending'])} approved={len(state['approved'])}")
    print(f"  Plan:    {len(actions)} actions queued")

    if not actions:
        print(f"  ✅ Nothing to do — system is idle")
        log.info(f"Cycle {cycle_num}: idle — no actions")
        return 0

    done_count = 0
    for i, action in enumerate(actions, 1):
        filepath = action["file"]
        action_type = action["action"]
        print(f"  Act [{i}/{len(actions)}]: {action_type} → {filepath.name}")

        try:
            if action_type == "move_inbox":
                result = act_move_inbox(filepath)
            elif action_type == "reason_and_draft":
                result = act_reason_and_draft(filepath)
            elif action_type == "auto_approve_low":
                result = act_auto_approve_low(filepath)
            else:
                result = f"Unknown action: {action_type}"
                continue

            # Verify
            ok = verify(action, result)
            status = "✅" if ok else "⚠️"
            print(f"    {status} {result}")
            if ok:
                done_count += 1

        except Exception as e:
            log.error(f"Action failed {action_type} on {filepath.name}: {e}")
            print(f"    ❌ Error: {e}")

    update_dashboard_status()
    print(f"\n  Summary: {done_count}/{len(actions)} actions completed")
    return done_count


# ─── Main ─────────────────────────────────────────────────────────────────────

def run_once(max_cycles: int = 1):
    print(f"\n{'='*50}")
    print(f"AutoOps AI — Ralph Wiggum Loop")
    print(f"{'='*50}")
    print(f"Max cycles: {max_cycles}")
    print(f"Vault: {VAULT.resolve()}")

    total_actions = 0
    for cycle in range(1, max_cycles + 1):
        actions_taken = run_cycle(cycle)
        total_actions += actions_taken
        if actions_taken == 0 and cycle > 1:
            print(f"\n✅ System idle after {cycle} cycles — stopping early")
            break

    print(f"\n{'='*50}")
    print(f"Ralph Loop complete: {total_actions} total actions across {cycle} cycle(s)")
    print(f"Plans created   : {len(list(PLANS.glob('*.md')))}")
    print(f"Pending approval: {len(list(PENDING.glob('*.md')))}")
    print(f"Done            : {len(list(DONE.glob('*.md')))}")
    log.info(f"Run complete: {total_actions} actions, {cycle} cycles")


def run_watch(interval: int = WATCH_INTERVAL):
    """Continuous autonomous operation."""
    print(f"Ralph Wiggum Loop — watching every {interval}s (Ctrl+C to stop)")
    log.info(f"Watch mode started (interval={interval}s)")
    cycle = 0
    while True:
        try:
            cycle += 1
            run_cycle(cycle)
            time.sleep(interval)
        except KeyboardInterrupt:
            print("\nRalph loop stopped.")
            break
        except Exception as e:
            log.error(f"Watch loop error: {e}")
            time.sleep(60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AutoOps AI — Ralph Wiggum Autonomous Loop")
    parser.add_argument("--cycles",   type=int, default=1,             help="Number of cycles to run (default: 1)")
    parser.add_argument("--watch",    action="store_true",              help="Continuous watch mode")
    parser.add_argument("--interval", type=int, default=WATCH_INTERVAL, help="Watch interval in seconds")
    args = parser.parse_args()

    if args.watch:
        run_watch(args.interval)
    else:
        run_once(args.cycles)
