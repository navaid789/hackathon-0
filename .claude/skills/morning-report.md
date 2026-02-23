# Skill: morning-report

Generate and save the daily morning briefing report for the CEO/manager.

## Instructions

1. Count files in each vault folder:
   - AI_Employee_Vault/Inbox/
   - AI_Employee_Vault/Needs_Action/
   - AI_Employee_Vault/Pending_Approval/
   - AI_Employee_Vault/Approved/
   - AI_Employee_Vault/Done/

2. Read last 3 entries from AI_Employee_Vault/Logs/system.log (if exists)

3. Detect priority breakdown in Needs_Action (high/medium/low keyword scan)

4. Generate report and save to:
   AI_Employee_Vault/Logs/morning_report_{YYYY-MM-DD}.md

Report format:
```
# Morning Briefing — {date}
Generated: {time}

## System Status
- Inbox:            {n} new items
- Needs Action:     {n} items requiring attention
- Pending Approval: {n} items awaiting your approval
- Completed Today:  {n} items in Done/

## Priority Breakdown
- High Priority:   {n} items
- Medium Priority: {n} items
- Low Priority:    {n} items

## Recommended Actions
1. {top priority item to handle first}
2. {second priority item}
3. {third item if any}

## System Health
- All watchers: Running
- Last activity: {timestamp from log}
```

5. Also call the /api/report endpoint and include API data if server is running
6. Print summary to terminal

## Usage
/morning-report
