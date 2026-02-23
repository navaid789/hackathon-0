# Skill: check-inbox

Check all vault folders and show a real-time status summary.

## Instructions

1. Count files in every folder:
   - AI_Employee_Vault/Inbox/
   - AI_Employee_Vault/Needs_Action/
   - AI_Employee_Vault/Pending_Approval/
   - AI_Employee_Vault/Approved/
   - AI_Employee_Vault/Done/
   - AI_Employee_Vault/Plans/
   - AI_Employee_Vault/Logs/

2. For Needs_Action and Pending_Approval, list each file with:
   - Filename
   - Priority (detected from content keywords)
   - Client (From field)

3. Display formatted status:
```
📊 AutoOps AI — Live Status
================================
📥 Inbox:             {n} new
⚡ Needs Action:      {n} items
   • {filename} | {priority} | {client}
📋 Pending Approval:  {n} items
   • {filename} | {priority} | {client}
✅ Approved (unsent): {n} items
📁 Done:              {n} completed
📝 Plans:             {n} plans
📓 Logs:              {n} log files
================================
```

4. If Pending_Approval has items, prompt: "Run /approve-task to review them"
5. If Needs_Action has items, prompt: "Run /triage-email to prioritize"

## Usage
/check-inbox
