# Skill: evening-summary

Generate end-of-day summary report for review.

## Instructions

1. Count all work done today:
   - Files in Done/ created/modified today
   - Files approved today (check Logs/system.log for today's APPROVED entries)
   - Files rejected today (REJECTED_ prefix in Done/)
   - Emails sent (check system.log for "Email sent" entries)

2. Read today's morning report from Logs/morning_report_{today}.md for comparison

3. Generate evening summary and save to:
   AI_Employee_Vault/Logs/evening_summary_{YYYY-MM-DD}.md

Format:
```
# Evening Summary — {date}
Generated: {time}

## Today's Accomplishments
- Tasks Completed:  {n}
- Emails Approved:  {n}
- Emails Rejected:  {n}
- Emails Sent:      {n}

## Still Pending
- Needs Action:     {n} items (carry over to tomorrow)
- Pending Approval: {n} items (review before EOD)

## Highlights
{list top 3 completed tasks}

## Tomorrow's Priorities
{list top items remaining in Needs_Action by priority}

## System Performance
- Zero crashes today: {yes/no from log}
- All watchers ran: {yes/no}
```

4. Update Dashboard.md with end-of-day stats
5. Print summary to terminal

## Usage
/evening-summary
