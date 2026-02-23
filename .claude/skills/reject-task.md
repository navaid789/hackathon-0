# Skill: reject-task

Reject a pending task and archive it with reason.

## Instructions

Given a filename in Pending_Approval/:

1. Read the file from AI_Employee_Vault/Pending_Approval/{filename}
2. Display the content
3. Ask: "Reason for rejection? (optional)"
4. Move file to AI_Employee_Vault/Done/REJECTED_{filename}
5. Log: "REJECTED: {filename} | Reason: {reason} | at {timestamp}"
6. Append to AI_Employee_Vault/Logs/system.log
7. Also call POST /api/reject/{filename} if API server is running
8. Print: "❌ Rejected. File archived to Done/REJECTED_{filename}"

## Usage
/reject-task {filename}
/reject-task (lists all pending, lets you choose)
