# Skill: update-dashboard

Refresh the AI_Employee_Vault/Dashboard.md with latest real-time data.

## Instructions

1. Count files in all vault folders (Inbox, Needs_Action, Pending_Approval, Approved, Done, Plans, Logs)

2. Get latest activity from AI_Employee_Vault/Logs/system.log (last 5 lines)

3. Detect current system state:
   - Are watchers running? (check for running python processes)
   - API server status (try GET http://localhost:8000/)
   - Flask dashboard status (try GET http://localhost:5000/)

4. Rewrite AI_Employee_Vault/Dashboard.md with:

```markdown
# AI Employee Dashboard
**Last Updated:** {datetime}

## System Status
| Service              | Status  |
|----------------------|---------|
| Filesystem Watcher   | {✅/❌}  |
| Gmail Watcher        | {✅/❌}  |
| Approval Watcher     | {✅/❌}  |
| FastAPI Backend      | {✅/❌}  |
| React Dashboard      | {✅/❌}  |

## Folder Status
| Folder           | Count |
|------------------|-------|
| Inbox            | {n}   |
| Needs Action     | {n}   |
| Pending Approval | {n}   |
| Approved         | {n}   |
| Done             | {n}   |
| Plans            | {n}   |

## Recent Activity (last 5 actions)
{last 5 log lines}

## Quick Actions
- /check-inbox — See all pending items
- /triage-email — Prioritize Needs_Action
- /draft-reply — Generate email replies
- /approve-task — Approve pending items
- /morning-report — Generate daily briefing
```

5. Print: "✅ Dashboard updated at {time}"

## Usage
/update-dashboard
