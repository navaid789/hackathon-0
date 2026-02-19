"""
AutoOps AI — FastAPI Backend
-----------------------------
Run karo:
    cd "/mnt/d/hackathon 0"
    uvicorn api.main:app --reload --port 8000

API Docs:
    http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pathlib import Path
from sqlalchemy.orm import Session
import shutil
import re
from datetime import datetime, timedelta
from api.database import init_db, get_db, TaskModel, EmailLogModel, AuditLogModel
from api.auth import (
    authenticate_user, create_token, get_current_user,
    require_manager_or_above, require_admin,
    Token, User, TOKEN_EXPIRE_MINUTES, log_audit
)

app = FastAPI(
    title="AutoOps AI",
    description="AI-powered Email Operations Assistant",
    version="1.0.0"
)

@app.on_event("startup")
def startup():
    init_db()  # Tables + default users banao

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


# ─── Auth Routes ─────────────────────────────────────────

@app.post("/api/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login karo — JWT token milega."""
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=401, detail="Username ya password galat hai")
    token = create_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    )
    log_audit(db, user.username, "login", f"Role: {user.role}")
    return Token(
        access_token=token,
        token_type="bearer",
        role=user.role,
        username=user.username
    )


@app.get("/api/auth/me", response_model=User)
def get_me(current_user: User = Depends(get_current_user)):
    """Apni profile dekho."""
    return current_user


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
def approve_task(
    filename: str,
    current_user: User   = Depends(require_manager_or_above),
    db:          Session = Depends(get_db)
):
    """File ko Pending_Approval se Approved mein move karo. (Manager+ only)"""
    name = safe_filename(filename)
    src  = VAULT / "Pending_Approval" / name
    dst  = VAULT / "Approved" / name
    if not src.exists():
        raise HTTPException(status_code=404, detail=f"{name} nahi mili")
    shutil.move(str(src), dst)

    # DB mein log karo
    db.add(EmailLogModel(filename=name, status="approved", action_by=current_user.username))
    log_audit(db, current_user.username, "approve", f"File: {name}")

    return {
        "message":     f"{name} approved!",
        "status":      "success",
        "approved_by": current_user.username,
        "timestamp":   datetime.now().isoformat()
    }


@app.post("/api/reject/{filename}")
def reject_task(
    filename: str,
    current_user: User   = Depends(require_manager_or_above),
    db:          Session = Depends(get_db)
):
    """File ko Pending_Approval se Done mein move karo. (Manager+ only)"""
    name = safe_filename(filename)
    src  = VAULT / "Pending_Approval" / name
    dst  = VAULT / "Done" / f"REJECTED_{name}"
    if not src.exists():
        raise HTTPException(status_code=404, detail=f"{name} nahi mili")
    shutil.move(str(src), dst)

    # DB mein log karo
    db.add(EmailLogModel(filename=name, status="rejected", action_by=current_user.username))
    log_audit(db, current_user.username, "reject", f"File: {name}")

    return {
        "message":     f"{name} rejected.",
        "status":      "rejected",
        "rejected_by": current_user.username,
        "timestamp":   datetime.now().isoformat()
    }


@app.get("/api/logs")
def get_logs():
    """System logs — last 50 lines."""
    log_file = VAULT / "Logs" / "system.log"
    if not log_file.exists():
        return {"logs": [], "message": "No logs yet."}
    lines = log_file.read_text(encoding="utf-8").splitlines()
    return {"logs": lines[-50:], "total_lines": len(lines)}


@app.get("/api/db/users")
def get_users(
    current_user: User   = Depends(require_admin),
    db:          Session = Depends(get_db)
):
    """Saare users dekho. (Admin only)"""
    from api.database import UserModel
    users = db.query(UserModel).all()
    return {"users": [{"username": u.username, "role": u.role, "full_name": u.full_name, "is_active": u.is_active, "created_at": str(u.created_at)} for u in users]}


@app.get("/api/db/audit")
def get_audit(
    current_user: User   = Depends(require_admin),
    db:          Session = Depends(get_db)
):
    """Audit log dekho. (Admin only)"""
    logs = db.query(AuditLogModel).order_by(AuditLogModel.created_at.desc()).limit(50).all()
    return {"audit_logs": [{"user": l.user, "action": l.action, "detail": l.detail, "time": str(l.created_at)} for l in logs]}


@app.get("/api/db/email-logs")
def get_email_logs(
    current_user: User   = Depends(get_current_user),
    db:          Session = Depends(get_db)
):
    """Email history dekho."""
    logs = db.query(EmailLogModel).order_by(EmailLogModel.created_at.desc()).limit(50).all()
    return {"email_logs": [{"filename": l.filename, "status": l.status, "action_by": l.action_by, "time": str(l.created_at)} for l in logs]}


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
