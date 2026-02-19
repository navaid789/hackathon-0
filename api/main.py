"""
AutoOps AI — FastAPI Backend
-----------------------------
Run karo:
    cd "/mnt/d/hackathon 0"
    uvicorn api.main:app --reload --port 8000

API Docs:
    http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import shutil
import re
from datetime import datetime

app = FastAPI(
    title="AutoOps AI",
    description="AI-powered Email Operations Assistant",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

VAULT   = Path("AI_Employee_Vault")
FOLDERS = ["Inbox", "Needs_Action", "Plans", "Pending_Approval", "Approved", "Done", "Logs"]

# Priority keywords for Phase 2 — Priority Detection
PRIORITY_KEYWORDS = {
    "urgent": "🔴 High",
    "asap":   "🔴 High",
    "invoice": "🟡 Medium",
    "meeting": "🟡 Medium",
    "follow":  "🟡 Medium",
    "hello":   "🟢 Low",
    "fyi":     "🟢 Low",
}


# ─── Security Helper ─────────────────────────────────────

def safe_filename(filename: str) -> str:
    """Path traversal se bachao — sirf safe filenames allow karo."""
    # Slash ya dot-dot hona nahi chahiye
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename — path traversal not allowed")
    name = Path(filename).name
    if not re.match(r'^[\w\-. ]+$', name):
        raise HTTPException(status_code=400, detail="Invalid filename — special characters not allowed")
    return name


# ─── Priority Detection (Phase 2) ────────────────────────

def detect_priority(content: str) -> str:
    """Email content se priority detect karo."""
    lower = content.lower()
    for keyword, priority in PRIORITY_KEYWORDS.items():
        if keyword in lower:
            return priority
    return "🟢 Low"


# ─── Client Tagging (Phase 2) ────────────────────────────

def detect_client(content: str, filename: str) -> str:
    """From field se client naam nikalo."""
    match = re.search(r'\*\*From:\*\*\s*(.+)', content)
    if match:
        return match.group(1).strip()
    if filename.startswith("EMAIL_"):
        return "Gmail Client"
    return "Unknown"


# ─── Folder Helper ───────────────────────────────────────

def folder_data(name: str):
    path = VAULT / name
    files = list(path.glob("*.md")) + list(path.glob("*.txt")) if path.exists() else []
    return {
        "count": len(files),
        "files": [
            {
                "name": f.name,
                "size": f.stat().st_size,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            }
            for f in files
        ]
    }


# ─── Routes ──────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "online", "product": "AutoOps AI", "version": "1.0.0"}


@app.get("/api/status")
def get_status():
    """Saare folders ka status."""
    return {folder: folder_data(folder) for folder in FOLDERS}


@app.get("/api/tasks")
def get_tasks():
    """Needs_Action mein saare tasks — with priority & client tag (Phase 2)."""
    path = VAULT / "Needs_Action"
    tasks = []
    for f in path.glob("*"):
        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            content = ""
        tasks.append({
            "name":     f.name,
            "content":  content[:500],
            "truncated": len(content) > 500,
            "priority": detect_priority(content),
            "client":   detect_client(content, f.name),
            "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        })
    # Sort by priority: High first
    priority_order = {"🔴 High": 0, "🟡 Medium": 1, "🟢 Low": 2}
    tasks.sort(key=lambda x: priority_order.get(x["priority"], 3))
    return {"tasks": tasks, "total": len(tasks)}


@app.get("/api/pending")
def get_pending():
    """Pending approval files — with priority & client."""
    path = VAULT / "Pending_Approval"
    items = []
    for f in path.glob("*.md"):
        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            content = ""
        items.append({
            "name":     f.name,
            "content":  content,
            "priority": detect_priority(content),
            "client":   detect_client(content, f.name),
            "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        })
    return {"pending": items, "total": len(items)}


@app.post("/api/approve/{filename}")
def approve_task(filename: str):
    """File ko Pending_Approval se Approved mein move karo."""
    name = safe_filename(filename)
    src  = VAULT / "Pending_Approval" / name
    dst  = VAULT / "Approved" / name
    if not src.exists():
        raise HTTPException(status_code=404, detail=f"{name} nahi mili")
    shutil.move(str(src), dst)
    return {"message": f"{name} approved!", "status": "success", "timestamp": datetime.now().isoformat()}


@app.post("/api/reject/{filename}")
def reject_task(filename: str):
    """File ko Pending_Approval se Done mein move karo (rejected)."""
    name = safe_filename(filename)
    src  = VAULT / "Pending_Approval" / name
    dst  = VAULT / "Done" / f"REJECTED_{name}"
    if not src.exists():
        raise HTTPException(status_code=404, detail=f"{name} nahi mili")
    shutil.move(str(src), dst)
    return {"message": f"{name} rejected.", "status": "rejected", "timestamp": datetime.now().isoformat()}


@app.get("/api/logs")
def get_logs():
    """System logs — last 50 lines."""
    log_file = VAULT / "Logs" / "system.log"
    if not log_file.exists():
        return {"logs": [], "message": "No logs yet."}
    lines = log_file.read_text(encoding="utf-8").splitlines()
    return {"logs": lines[-50:], "total_lines": len(lines)}


@app.get("/api/report")
def get_report():
    """CEO daily report with priority breakdown."""
    done    = list((VAULT / "Done").glob("*.md"))
    pending = list((VAULT / "Pending_Approval").glob("*.md"))
    needs   = list((VAULT / "Needs_Action").glob("*"))

    # Priority breakdown for Needs_Action
    high = medium = low = 0
    for f in needs:
        try:
            content = f.read_text(encoding="utf-8")
            p = detect_priority(content)
            if "High"   in p: high   += 1
            elif "Medium" in p: medium += 1
            else:               low    += 1
        except Exception:
            low += 1

    return {
        "date":             datetime.now().strftime("%Y-%m-%d"),
        "tasks_completed":  len(done),
        "pending_approval": len(pending),
        "needs_action":     len(needs),
        "total_processed":  len(done) + len(pending) + len(needs),
        "priority_breakdown": {
            "high":   high,
            "medium": medium,
            "low":    low
        }
    }
