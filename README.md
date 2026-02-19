# AI Email Operations Assistant

An automated AI-powered email operations system that reads incoming emails, generates draft replies, implements a human-in-the-loop approval workflow, and sends automated responses.

## Features

- Automated email detection via Gmail API
- Folder-based task workflow (Inbox → Needs Action → Plans → Approval → Done)
- Human approval system before any email is sent
- Live dashboard UI (browser-based)
- Daily CEO report & scheduled updates
- Logging and crash recovery
- Automated tests with pytest

## Tech Stack

- Python 3.12+
- Gmail API + OAuth 2.0
- Flask (Dashboard UI)
- Schedule (Task Automation)
- Pytest (Testing)
- Watchdog-style folder monitoring

## Project Structure

```
AI-Email-Operations/
│
├── watchers/
│   ├── gmail_watcher.py        # Detects new emails
│   └── approval_watcher.py     # Sends approved emails
│
├── orchestration/
│   ├── orchestrator.py         # Runs all watchers together
│   ├── scheduler.py            # Timed automation (9am, 6pm, 30min)
│   ├── dashboard_updater.py    # Updates dashboard counts
│   └── ceo_report.py          # Daily summary report
│
├── tests/
│   └── test_dashboard.py       # Automated tests
│
├── scripts/
│   ├── start.bat               # Windows one-click start
│   └── stop.bat                # Windows one-click stop
│
├── AI_Employee_Vault/          # Workflow folders
│   ├── Inbox/
│   ├── Needs_Action/
│   ├── Plans/
│   ├── Pending_Approval/
│   ├── Approved/
│   ├── Done/
│   └── Logs/
│
├── dashboard_ui.py             # Browser dashboard (localhost:5000)
├── filesystem_watcher.py       # Folder monitor
└── run_system.py               # Master runner (starts everything)
```

## Workflow

```
Email Received
      ↓
gmail_watcher.py → Needs_Action/EMAIL_xxx.md
      ↓
AI reads & creates → Plans/plan_xxx.md
      ↓
Draft → Pending_Approval/
      ↓
Human reviews & approves
      ↓
approval_watcher.py → Gmail sends email
      ↓
Done/ ✓
```

## Quick Start

**1. Install dependencies:**
```bash
pip install flask schedule pytest google-api-python-client google-auth-oauthlib
```

**2. Add Gmail credentials:**
- Go to [Google Cloud Console](https://console.cloud.google.com)
- Create OAuth 2.0 credentials → Download as `credentials.json`
- Place in project root

**3. Run everything:**
```bash
python run_system.py
```

**4. Open dashboard:**
```
http://localhost:5000
```

## Running Tests

```bash
pytest tests/ -v
```

## Key Design Decisions

- **Human-in-the-loop**: No email is sent without human approval
- **Crash recovery**: All watchers wrapped in try/except with logging
- **Dry run mode**: Works without Gmail credentials for testing
- **Modular architecture**: Each component is independent and replaceable

## Resume Impact

- Designed modular automation architecture using folder-based workflow tracking
- Implemented approval-based email automation to simulate real business operations
- Integrated Gmail API for automated reading and sending of emails
- Built live dashboard with scheduled reporting and auto-refresh
- Added production-level logging and crash recovery

## Author

Built as part of AI automation hackathon project.
