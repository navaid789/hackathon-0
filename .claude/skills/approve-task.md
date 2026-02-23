# Skill: approve-task

Approve a pending task and move it through the workflow.

## Instructions

Given a filename in Pending_Approval/:

1. Read the file from AI_Employee_Vault/Pending_Approval/{filename}
2. Display the content clearly:
   - To, Subject, Priority, Client, Body
3. Ask for confirmation: "Approve this email reply? (yes/no)"
4. If approved:
   - Move file to AI_Employee_Vault/Approved/{filename}
   - Log action: "APPROVED: {filename} by human at {timestamp}"
   - Append to AI_Employee_Vault/Logs/system.log
   - Also call POST /api/approve/{filename} if API server is running
   - Print: "✅ Approved! Moving to Approved/ folder. Approval watcher will send the email."
5. If rejected:
   - Call /reject-task skill instead

## Usage
/approve-task {filename}
/approve-task (lists all pending and lets you choose)
