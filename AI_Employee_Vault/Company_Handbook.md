# Company Handbook — AutoOps AI

**Version:** 1.0
**Last Updated:** 2026-02-25
**Owner:** Operations Team

---

## 1. About AutoOps AI

AutoOps AI is your autonomous Digital FTE (Full-Time Employee) that handles email operations, task triage, and business communications. It works 24/7, never misses an email, and always waits for human approval before sending anything.

**Core Mission:** Handle email volume so the team can focus on high-value work.

---

## 2. Autonomy Levels

AutoOps AI operates on a 3-level autonomy model:

| Level | Action | Human Required? |
|-------|--------|-----------------|
| **Level 1 — Auto** | Read emails, detect priority, create plans | ❌ No |
| **Level 2 — Approval** | Draft replies, move to Pending_Approval | ✅ Yes — review before sending |
| **Level 3 — Restricted** | Send emails, post on LinkedIn, external API calls | ✅ Yes — explicit approval |

> **Rule:** AutoOps AI NEVER sends an email or posts publicly without human approval.

---

## 3. Folder Workflow

```
/Inbox              → New raw emails (watchers deposit here)
  ↓ (filesystem_watcher.py)
/Needs_Action       → Triage + reasoning loop processes here
  ↓ (reasoning_loop.py → Claude AI)
/Plans              → Auto-generated action plans (Plan.md files)
  ↓
/Pending_Approval   → Draft replies waiting for human review
  ↓ (Human approves via dashboard or API)
/Approved           → Approved — ready to send
  ↓ (approval_watcher.py)
/Done               → Completed tasks (sent emails, closed items)
/Logs               → System logs, morning reports, evening summaries
```

---

## 4. Priority Definitions

| Priority | Keywords | Response Time |
|----------|----------|---------------|
| 🔴 HIGH | urgent, ASAP, immediately, critical, overdue, invoice, payment | Within 1 hour |
| 🟡 MEDIUM | meeting, schedule, follow-up, proposal, contract, review | Within 4 hours |
| 🟢 LOW | newsletter, FYI, update, general info | Within 24 hours |

---

## 5. Safety Rules

1. **No autonomous sending** — All outgoing emails must pass through Pending_Approval
2. **No path traversal** — File operations restricted to vault directories only
3. **No credential exposure** — credentials.json and token files are gitignored
4. **Audit trail** — Every approve/reject/login action is logged to the database
5. **DRY_RUN default** — All external integrations default to simulation mode
6. **Role-based access** — Admin / Manager / Viewer permissions enforced via JWT

---

## 6. User Roles

| Role | Can Do |
|------|--------|
| **Admin** | View all logs, manage users, approve/reject, full access |
| **Manager** | Approve/reject tasks, view reports, view audit logs |
| **Viewer** | View dashboard and status only — read-only |

**Default Credentials (change in production):**
- Admin: `admin` / `admin123`
- Manager: `manager` / `manager123`
- Viewer: `viewer` / `viewer123`

---

## 7. Agent Skills Reference

All AI functionality is implemented as Claude Code skills in `.claude/skills/`:

| Skill | Command | What it does |
|-------|---------|--------------|
| check-inbox | `/check-inbox` | Live folder status |
| triage-email | `/triage-email` | Prioritize Needs_Action |
| draft-reply | `/draft-reply` | Generate email drafts |
| reasoning-loop | `/reasoning-loop` | AI reasoning → Plan.md |
| approve-task | `/approve-task` | Approve pending item |
| reject-task | `/reject-task` | Reject and archive |
| morning-report | `/morning-report` | Daily CEO briefing |
| evening-summary | `/evening-summary` | End-of-day summary |
| send-email | `/send-email` | Send via Gmail API |
| post-linkedin | `/post-linkedin` | LinkedIn business post |
| update-dashboard | `/update-dashboard` | Refresh Dashboard.md |

---

## 8. MCP Servers

| Server | Tools | Purpose |
|--------|-------|---------|
| `autoops-vault` | 8 tools | Vault folder operations |
| `autoops-dashboard` | 5 tools | Reports and status |
| `autoops-gmail` | 4 tools | Email send/receive |

---

## 9. Tech Stack

- **Brain:** Claude Code (Sonnet 4.6)
- **Memory/GUI:** Obsidian vault (AI_Employee_Vault/)
- **Backend:** FastAPI (port 8000) + SQLAlchemy
- **Frontend:** React + Vite (port 5173)
- **Auth:** JWT + bcrypt (3 roles)
- **Watchers:** Python (Filesystem, Gmail, Approval, LinkedIn)
- **Scheduler:** Python schedule library (09:00 / 18:00)
- **MCP Servers:** Node.js (@modelcontextprotocol/sdk)
- **Database:** SQLite (dev) / PostgreSQL (prod via DATABASE_URL)
- **Tests:** pytest — 11 tests, all passing

---

## 10. Environment Variables

```bash
# Required for live Gmail:
ANTHROPIC_API_KEY=your_claude_api_key

# Required for live LinkedIn posting:
LINKEDIN_ACCESS_TOKEN=your_linkedin_token

# Production database:
DATABASE_URL=postgresql://user:pass@host/dbname

# JWT secret (change in production!):
SECRET_KEY=your-secret-key-change-in-production
```

---

## 11. Quick Start

```bash
# Install dependencies
uv sync   # or: pip install -r requirements.txt

# Start all services
python run_system.py

# Or individually:
python filesystem_watcher.py          # File monitoring
python watchers/gmail_watcher.py      # Gmail monitoring
python watchers/approval_watcher.py   # Send approved emails
python watchers/linkedin_watcher.py   # LinkedIn auto-posts
python orchestration/reasoning_loop.py # AI planning loop
python orchestration/scheduler.py     # Daily reports
uvicorn api.main:app --port 8000      # REST API
python dashboard_ui.py                # Flask dashboard

# Run tests
python -m pytest tests/ -v
```

---

*This handbook is the source of truth for AutoOps AI behavior. Update it as the system evolves.*
