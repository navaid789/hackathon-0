# AutoOps AI — Architecture & Lessons Learned

## Overview

AutoOps AI is an autonomous Digital FTE (Full-Time Employee) built for the Hackathon. It handles email operations, task triage, business communications, social media posting, and accounting integration — with human-in-the-loop approval for all sensitive actions.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     HUMAN INTERFACE                          │
│  React Dashboard (5173) │ Flask UI (5000) │ Claude Code CLI  │
└──────────────┬──────────────────────────────────┬───────────┘
               │                                  │
┌──────────────▼──────────────────┐  ┌────────────▼────────────┐
│      FastAPI Backend (8000)     │  │    Agent Skills          │
│  JWT Auth │ RBAC │ 13 endpoints │  │  .claude/skills/ (11)    │
│  SQLAlchemy │ Audit Logs        │  │  /triage-email           │
│  SQLite → PostgreSQL ready      │  │  /draft-reply            │
└──────────────┬──────────────────┘  │  /approve-task           │
               │                     │  /reasoning-loop         │
┌──────────────▼──────────────────┐  │  /post-linkedin          │
│         OBSIDIAN VAULT          │  │  /weekly-audit           │
│   AI_Employee_Vault/            │  └─────────────────────────┘
│   Inbox → Needs_Action →        │
│   Plans → Pending_Approval →    │
│   Approved → Done               │
│   Logs/   Plans/                │
└───────────────┬─────────────────┘
                │
┌───────────────▼─────────────────────────────────────────────┐
│                    WATCHER LAYER                              │
│  filesystem_watcher.py  │  gmail_watcher.py                  │
│  approval_watcher.py    │  linkedin_watcher.py               │
│  social_media_watcher.py (Facebook, Instagram, Twitter)      │
└───────────────┬─────────────────────────────────────────────┘
                │
┌───────────────▼─────────────────────────────────────────────┐
│              ORCHESTRATION LAYER                              │
│  orchestrator.py    — manages 5 watcher processes            │
│  scheduler.py       — 09:00 morning, 18:00 evening reports   │
│  reasoning_loop.py  — Claude AI → Plan.md auto-generator     │
│  ralph_loop.py      — Observe→Plan→Act→Verify autonomous loop│
│  weekly_audit.py    — Monday 08:00 business audit            │
│  ceo_report.py      — Daily CEO summary                      │
└───────────────┬─────────────────────────────────────────────┘
                │
┌───────────────▼─────────────────────────────────────────────┐
│                   MCP SERVER LAYER                            │
│  vault_server.js     — 8 tools (file operations)             │
│  dashboard_server.js — 5 tools (status, reports)             │
│  gmail_server.js     — 4 tools (email send/receive)          │
│  odoo_server.js      — 7 tools (accounting, invoices, CRM)   │
└───────────────┬─────────────────────────────────────────────┘
                │
┌───────────────▼─────────────────────────────────────────────┐
│                  EXTERNAL INTEGRATIONS                        │
│  Gmail API (OAuth2)  │  LinkedIn API  │  Facebook Graph API  │
│  Instagram API       │  Twitter API v2 │  Odoo JSON-RPC       │
└─────────────────────────────────────────────────────────────┘
```

---

## Folder Flow (The Pipeline)

```
Email arrives in Gmail
        ↓
gmail_watcher.py detects it
        ↓
Saved as EMAIL_{id}.md → AI_Employee_Vault/Inbox/
        ↓
filesystem_watcher.py moves it → Needs_Action/
        ↓
reasoning_loop.py / ralph_loop.py analyzes it (Claude AI)
        ↓
Plan saved → Plans/plan_{name}.md
Draft reply → Pending_Approval/{name}.md
        ↓
[HUMAN REVIEWS via React Dashboard or API]
        ↓
     Approve?
    ✅ Yes → Approved/{name}.md
    ❌ No  → Done/REJECTED_{name}.md
        ↓
approval_watcher.py detects Approved/ file
        ↓
Gmail API sends the email → Done/{name}.md
```

---

## Key Design Decisions

### 1. Human-in-the-Loop by Default
**Decision:** No email is ever sent without human approval.
**Why:** Trust and reliability. An AI that sends wrong emails destroys business relationships.
**Implementation:** Pending_Approval folder acts as a mandatory gate. FastAPI endpoints `/approve` and `/reject` require JWT authentication.

### 2. Folder-Based State Machine
**Decision:** Use filesystem folders as the workflow state machine instead of a database queue.
**Why:** Obsidian-native, human-readable, easy to inspect and debug. Any state is visible by just opening the vault.
**Trade-off:** Not atomic (race conditions possible with multiple watchers). Solved with processed.txt tracking and sleep intervals.

### 3. DRY_RUN Default
**Decision:** All external actions (email send, LinkedIn post, Odoo writes) default to dry-run simulation.
**Why:** Safety first. Cannot accidentally spam clients or post to social media during development.
**Implementation:** Each watcher checks for credentials/tokens before going live. Missing = simulate.

### 4. Role-Based Access Control (3 Levels)
**Decision:** Admin / Manager / Viewer roles with JWT tokens.
**Why:** In a real business, not everyone should approve emails or view audit logs.
**Implementation:** FastAPI dependency injection — `require_admin()`, `require_manager_or_above()`, `get_current_user()`.

### 5. SQLite → PostgreSQL via Env Var
**Decision:** Use SQLAlchemy ORM with DATABASE_URL env var.
**Why:** Zero code changes to go from development (SQLite) to production (PostgreSQL).
**Implementation:** `DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./autoops.db")`

### 6. Ralph Wiggum Loop (Autonomous Agent)
**Decision:** Observe → Plan → Act → Verify cycle for autonomous multi-step execution.
**Why:** The hackathon required autonomous task completion without human intervention for each micro-step.
**Key insight:** AUTO-APPROVE only for LOW priority (newsletters, FYIs). HIGH and MEDIUM always require human review.

### 7. MCP Servers in Node.js
**Decision:** Build MCP servers in Node.js using `@modelcontextprotocol/sdk`.
**Why:** The MCP SDK is most mature in TypeScript/JavaScript. Python wrappers exist but are less stable.
**Trade-off:** Mixed Python/Node.js stack. Solved with `gmail_helper.py` as a Python subprocess bridge.

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| AI Brain | Claude Code (Sonnet 4.6) | Best reasoning for business tasks |
| Backend API | FastAPI | Fast, type-safe, auto-docs |
| Frontend | React + Vite | Modern, fast hot reload |
| Auth | JWT + bcrypt | Industry standard, stateless |
| Database | SQLAlchemy + SQLite/PostgreSQL | ORM flexibility |
| Watchers | Python (watchdog, schedule) | Simple, reliable |
| MCP Servers | Node.js + @modelcontextprotocol/sdk | Native MCP support |
| Memory/GUI | Obsidian Vault | Human-readable, markdown-native |
| Accounting | Odoo 19+ (JSON-RPC) | Open-source ERP |
| Social | Facebook Graph, Twitter v2, LinkedIn | Major business platforms |
| Tests | pytest | 11 tests, all passing |
| CI/CD | GitHub | Version control + collaboration |

---

## Lessons Learned

### What Worked Well

1. **Folder-as-state-machine** — Incredibly powerful for visibility and debugging. You can literally see the system's state by listing files.

2. **DRY_RUN first** — Starting every integration in simulation mode meant we could build and test without fear of accidental side effects.

3. **Agent Skills** — Converting all AI functionality into `.claude/skills/` markdown files made the system self-documenting and very easy to extend.

4. **SQLAlchemy ORM** — The ability to switch from SQLite to PostgreSQL with zero code changes is invaluable for production readiness.

5. **JWT with refresh in mind** — Building role-based access from day one made adding the React dashboard trivial.

### What Was Hard

1. **WSL2 + Windows Credential Manager** — Git push always intercepted by Windows. Solution: clone via `gh` CLI, rsync files, push from clone.

2. **Race conditions with multiple watchers** — Both filesystem_watcher and scheduler were moving Inbox files. Solution: centralize all Inbox monitoring in one place.

3. **Gmail OAuth in headless environment** — Browser flow doesn't work in WSL2. Solution: use `run_local_server(port=0)` and manually open browser.

4. **MCP server process management** — Node.js MCP servers need to stay alive as stdio processes. Complex with multiple servers. Solution: `settings.json` with separate process per server.

5. **Priority detection accuracy** — Simple keyword matching gives false positives (e.g., "meeting notes" tagged as MEDIUM when it's just an FYI). A better approach would be embeddings-based classification.

### What I'd Do Differently

1. Use **asyncio** throughout Python watchers instead of sleep loops
2. Add **Redis pub/sub** for real-time updates instead of polling
3. Use **Celery** for task queue instead of folder-based state
4. **Vector database** for semantic email similarity search
5. **Webhooks** instead of polling for Gmail (Gmail Push Notifications)
6. Add **end-to-end encryption** for sensitive email content at rest

---

## File Structure

```
hackathon 0/
├── .claude/
│   ├── settings.json          # MCP server registration
│   └── skills/                # 11 Agent Skills
├── AI_Employee_Vault/         # Obsidian Vault
│   ├── Dashboard.md
│   ├── Company_Handbook.md
│   ├── Inbox/
│   ├── Needs_Action/
│   ├── Pending_Approval/
│   ├── Approved/
│   ├── Done/
│   ├── Plans/
│   └── Logs/
├── api/
│   ├── main.py                # FastAPI (13 endpoints)
│   ├── auth.py                # JWT + bcrypt + RBAC
│   └── database.py            # SQLAlchemy models
├── frontend/
│   └── src/
│       ├── App.jsx            # React dashboard
│       └── Login.jsx          # JWT login page
├── mcp_servers/
│   ├── vault_server.js        # 8 tools
│   ├── dashboard_server.js    # 5 tools
│   ├── gmail_server.js        # 4 tools
│   ├── odoo_server.js         # 7 tools
│   └── gmail_helper.py        # Python Gmail bridge
├── orchestration/
│   ├── orchestrator.py        # Process manager
│   ├── scheduler.py           # Daily reports
│   ├── reasoning_loop.py      # AI → Plan.md
│   ├── ralph_loop.py          # Autonomous agent loop
│   ├── weekly_audit.py        # Weekly CEO briefing
│   └── ceo_report.py          # Daily CEO report
├── watchers/
│   ├── gmail_watcher.py       # Gmail API monitor
│   ├── approval_watcher.py    # Send approved emails
│   ├── linkedin_watcher.py    # LinkedIn auto-post
│   └── social_media_watcher.py # FB + IG + Twitter
├── tests/
│   └── test_dashboard.py      # 11 pytest tests
├── filesystem_watcher.py      # Inbox monitor
├── dashboard_ui.py            # Flask dashboard (5000)
├── run_system.py              # Master runner
├── pyproject.toml             # UV project config
├── ARCHITECTURE.md            # This file
└── README.md                  # GitHub readme
```

---

## Running the Full System

```bash
# Option 1: All at once
python run_system.py

# Option 2: Individual components
python filesystem_watcher.py &
python watchers/gmail_watcher.py &
python watchers/approval_watcher.py &
python watchers/linkedin_watcher.py --watch &
python watchers/social_media_watcher.py --watch &
python orchestration/reasoning_loop.py --watch &
python orchestration/ralph_loop.py --watch &
python orchestration/scheduler.py &
python orchestration/weekly_audit.py --watch &
uvicorn api.main:app --port 8000 &
python dashboard_ui.py &

# Option 3: Orchestrator (manages restarts)
python orchestration/orchestrator.py
```

---

*AutoOps AI — Hackathon Project 2026*
*Built with Claude Code + Python + React + Node.js*
